import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from decimal import Decimal
from auth.access import group_required
from database.sql_provider import SQLProvider
from database.select import select_list
from model_route import model_route, ResultInfo

blueprint_banquet = Blueprint('bp_banquet', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))





# Шаг 1–3 — без изменений (кроме удаления аванса из шага 3)
@blueprint_banquet.route('/', methods=['GET'])
@group_required
def banquet_start():
    session.pop('banquet_order', None)
    return render_template('banquet_step1_people.html')


@blueprint_banquet.route('/step1', methods=['POST'])
@group_required
def step1_people():
    num = request.form.get('number_of_people')
    if not num or int(num) <= 0:
        return render_template('banquet_step1_people.html', error='Укажите количество гостей')
    session['banquet_order'] = {'number_of_people': num} # сохраняет в сессию
    session.modified = True
    return redirect(url_for('bp_banquet.step2_hall'))


@blueprint_banquet.route('/step2', methods=['GET', 'POST'])
@group_required
def step2_hall():
    if 'banquet_order' not in session:
        return redirect(url_for('bp_banquet.banquet_start'))

    num_people = session['banquet_order']['number_of_people']
    halls = select_list(provider.get('get_halls.sql'), [num_people])

    if request.method == 'POST':
        hall_id = request.form.get('hall_id')
        if not hall_id:
            return render_template('banquet_step2_hall.html', halls=halls, number_of_people=num_people,
                                   error='Выберите зал')
        session['banquet_order']['hall_id'] = hall_id
        session.modified = True # используется для явного указания того, что объект сессии был изменён и его следует сохранить.
        return redirect(url_for('bp_banquet.step3_details'))

    return render_template('banquet_step2_hall.html', halls=halls, number_of_people=num_people)


@blueprint_banquet.route('/step3', methods=['GET', 'POST'])
@group_required
def step3_details():
    if 'banquet_order' not in session or 'hall_id' not in session['banquet_order']:
        return redirect(url_for('bp_banquet.banquet_start'))

    managers = select_list(provider.get('get_managers.sql'), []) # Получает список менеджеров
    today = datetime.now().strftime('%Y-%m-%d')
    order = session['banquet_order']

    if request.method == 'POST':
        date = request.form.get('order_date')
        time = request.form.get('order_time')
        manager_id = request.form.get('manager_id')

        if not all([date, time, manager_id]):
            return render_template('banquet_step3_details.html', managers=managers, today=today,
                                   error='Заполните все поля')

        order.update({
            'order_date': date,
            'order_time': time,
            'manager_id': manager_id,
            'avance': '0'  # аванс по умолчанию
        })
        session.modified = True
        return redirect(url_for('bp_banquet.step4_menu'))

    return render_template('banquet_step3_details.html',
                           managers=managers,
                           today=today,
                           order_date=order.get('order_date'),
                           order_time=order.get('order_time'),
                           manager_id=order.get('manager_id'))


@blueprint_banquet.route('/step4', methods=['GET', 'POST'])
@group_required
def step4_menu():
    if 'banquet_order' not in session or 'order_date' not in session['banquet_order']:
        return redirect(url_for('bp_banquet.banquet_start'))

    menu_items_raw = select_list(provider.get('get_menu.sql'), [])
    order = session['banquet_order'] # Текущие детали заказа (зал, дата, менеджер)
    cart_dict = order.get('cart_data', {}) # Содержимое корзины (словарь {id: кол-во})
    error = None

    if request.method == 'POST':
        action = request.form.get('action') # # Определяем, какое действие запросил пользователь3

        # Добавление в корзину одной кнопкой
        if action == 'add_to_cart':
            updated = False
            for key in request.form:
                if key.startswith('quantity_'):
                    menu_id = key.split('_')[1]
                    if request.form.get(f'selected_{menu_id}') == '1':  # только отмеченные
                        try:
                            qty = int(request.form.get(key, '0'))
                            if qty > 0:
                                current = int(cart_dict.get(menu_id, '0'))
                                new_qty = current + qty
                                if new_qty > 0:
                                    cart_dict[menu_id] = str(new_qty)
                                    updated = True
                                else:
                                    cart_dict.pop(menu_id, None)
                                    updated = True
                        except ValueError:
                            error = 'Некорректное количество'
                            break
            if updated:
                order['cart_data'] = cart_dict
                session.modified = True

        # Очистка корзины
        elif action == 'clear_cart':
            order['cart_data'] = {}
            session.modified = True
            cart_dict = {}

        # Обновление аванса
        elif action == 'update_avance':
            try:
                avance = Decimal(request.form.get('avance', '0').strip())
                if avance < 0:
                    raise ValueError
                order['avance'] = str(avance)
                session.modified = True
            except:
                error = 'Некорректная сумма аванса'

        # Оформление заказа
        elif action == 'checkout':
            total_cost, cart_items_template, selected_items = calculate_cart_data(cart_dict, menu_items_raw)

            if not selected_items:
                error = 'Корзина пуста'
            else:
                try:
                    avance = Decimal(order.get('avance', '0'))
                    user_input = {
                        'hall_id': int(order['hall_id']),
                        'number_of_people': int(order['number_of_people']),
                        'manager_id': int(order['manager_id']),
                        'avance': avance,
                        'order_date': order['order_date'],
                        'order_time': order['order_time'],
                        'total_cost': Decimal(str(total_cost)),
                        'selected_items': selected_items
                    }

                    result_info: ResultInfo = model_route(
                        provider=provider,
                        user_input=user_input,
                        sql_file='banquet_order'
                    )

                    if result_info.status:
                        session.pop('banquet_order', None)
                        return redirect(url_for('bp_banquet.order_success'))
                    else:
                        error = result_info.err_message or 'Ошибка сохранения заказа'
                except Exception as e:
                    error = f'Ошибка: {str(e)}'

        # Пересчёт после любого POST
        total_cost, cart_items_template, _ = calculate_cart_data(cart_dict, menu_items_raw)
        current_avance = order.get('avance', '0')

        return render_template('banquet_step4_menu.html',
                               menu_items=menu_items_raw,
                               cart_items=cart_items_template,
                               total_cost=total_cost,
                               avance=current_avance,
                               error=error)

    # GET
    total_cost, cart_items_template, _ = calculate_cart_data(cart_dict, menu_items_raw)
    current_avance = order.get('avance', '0')

    return render_template('banquet_step4_menu.html',
                           menu_items=menu_items_raw,
                           cart_items=cart_items_template,
                           total_cost=total_cost,
                           avance=current_avance)


@blueprint_banquet.route('/success', methods=['GET'])
@group_required
def order_success():
    return render_template('banquet_success.html')


def get_menu_item_details(menu_items, menu_id): # Находит информацию о конкретном блюде
    for item in menu_items:
        if str(item[0]) == str(menu_id):
            return {'id': item[0], 'name': item[1], 'price': float(item[2])}
    return None


def calculate_cart_data(cart_dict, menu_items_raw):
    total_cost = 0.0
    selected_items_for_db = []
    cart_items_for_template = []

    for menu_id_str, quantity_str in cart_dict.items():
        try:
            menu_id = int(menu_id_str)
            quantity = int(quantity_str)
            if quantity > 0:
                item_details = get_menu_item_details(menu_items_raw, menu_id)
                if item_details:
                    price = item_details['price']
                    subtotal = price * quantity
                    total_cost += subtotal

                    selected_items_for_db.append((menu_id, quantity))
                    cart_items_for_template.append({
                        'id': menu_id,
                        'name': item_details['name'],
                        'price': price,
                        'quantity': quantity,
                        'subtotal': subtotal
                    })
        except ValueError:
            continue

    return total_cost, cart_items_for_template, selected_items_for_db

# total_cost: Общая стоимость заказа (число с плавающей точкой).
#
# cart_items_for_template: Список словарей, удобный для отображения в шаблоне (с именем, ценой, количеством и подытогом).
#
# selected_items_for_db: Список кортежей [(menu_id, quantity)], готовый для передачи в транзакцию базы данных.
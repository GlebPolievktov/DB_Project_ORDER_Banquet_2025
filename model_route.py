from dataclasses import dataclass
from database.select import select_list
from database.DB_context_manager import DBContextManager
from flask import current_app



@dataclass
class ResultInfo: 
    result: tuple
    status: bool
    err_message: str


def model_route(provider, user_input: dict, sql_file='1.sql'):
    err_message = ''

    # обрабатывает логику оформления заказа на банкет
    if sql_file == 'banquet_order':
        try:
            # Получаем SQL-запросы для транзакции
            sql_next_order_id = provider.get('get_next_order_id.sql')
            sql_insert_order = provider.get('insert_order.sql')
            sql_insert_details = provider.get('insert_order_details.sql')

            # Извлекаем параметры заказа
            manager_id = user_input['manager_id']
            hall_id = user_input['hall_id']
            order_date = user_input['order_date']
            order_time = user_input['order_time']
            avance = user_input['avance']
            number_of_people = user_input['number_of_people']
            total_cost = user_input['total_cost']
            selected_items = user_input['selected_items']

            with DBContextManager(current_app.config['db_config']) as cursor:
                if cursor is None:
                    raise ValueError('Не удалось подключиться к БД')

                # 1. Получаем следующий order_id
                cursor.execute(sql_next_order_id)
                next_order_id = cursor.fetchone()[0]

                plan_num_people = number_of_people
                plan_cost = total_cost

                # 2. Вставляем заказ в таблицу 'Order'
                cursor.execute(
                    sql_insert_order,
                    [next_order_id, int(manager_id), hall_id, order_date, order_time, float(avance),
                     plan_num_people, number_of_people, total_cost, plan_cost]
                )

                # 3. Вставляем детали заказа в таблицу 'Order_Datails'
                for menu_id, quantity in selected_items:
                    cursor.execute(
                        sql_insert_details,
                        [menu_id, next_order_id, quantity, quantity]
                    )

            success_message = (('Заказ успешно создан',),)
            return ResultInfo(result=success_message, status=True, err_message='')

        except Exception as e:
            err_message = f'Ошибка при выполнении транзакции заказа: {str(e)}'
            return ResultInfo(result=None, status=False, err_message=err_message)

    try:
        _sql = provider.get(sql_file)
    except KeyError:
        err_message = f"SQL-файл '{sql_file}' не найден."
        return ResultInfo(result=None, status=False, err_message=err_message)

    params = []

    if sql_file == 'get_halls.sql':
        params = [user_input.get('number_of_people')]
    elif sql_file == 'auth.sql':
        params = [user_input.get('login', '')]
    elif 'report' in sql_file:
        month = user_input.get('month')
        year = user_input.get('year')
        if month and year:
            params = [month, year]
        else:
            err_message = 'Не указаны месяц и/или год для отчёта'
            return ResultInfo(result=None, status=False, err_message=err_message)
    elif 'report' not in sql_file:
        query_type = user_input.get('query_type', 'category')
        if query_type == 'category':
            params = [user_input.get('prod_category', '')]
        elif query_type == 'price':
            min_price = user_input.get('min_price', 0)
            max_price = user_input.get('max_price', 1000)
            params = [min_price, max_price]
        else:
            params = []
    else:
        params = [user_input.get('month'), user_input.get('year')]


    try:
        result = select_list(_sql, params)

        if result:
            return ResultInfo(result=result, status=True, err_message=err_message)


        elif sql_file == 'get_halls.sql':
            err_message = 'Не найдено подходящих залов.'
            return ResultInfo(result=None, status=False, err_message=err_message)

        elif 'create' in sql_file:
            success_message = (('Отчёт успешно создан',),)
            return ResultInfo(result=success_message, status=True, err_message='')

        else:
            err_message = 'Данные не получены - пустой результат'
            return ResultInfo(result=None, status=False, err_message=err_message)

    except Exception as e:
        err_message = f'Ошибка при выполнении запроса: {str(e)}'

        return ResultInfo(result=None, status=False, err_message=err_message)

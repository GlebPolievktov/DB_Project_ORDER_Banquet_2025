import os
from flask import Blueprint, render_template, request,redirect,url_for

from auth.access import login_required, group_required
from database.sql_provider import SQLProvider
from model_route import model_route

blueprint_query = Blueprint('bp_query', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

@blueprint_query.route('/', methods=['GET'])
@login_required
@group_required
def menu_handler():
    return render_template('query_menu.html')


@blueprint_query.route('/<query_type>', methods=['GET'])
@login_required
@group_required
def query_type_handler(query_type):
    titles = {
        'category': 'Информация об менеджерах',
        'price': 'Стоимсоть банкета по диапазону цен'
    }

    query_type_text = titles.get(query_type)

    if query_type_text:

        return render_template('query.html', query_type=query_type, query_type_text=query_type_text)
    else:
        return redirect(url_for('bp_query.menu_handler'))

@blueprint_query.route('/execute', methods=['POST'])
def result_handler():
    user_input = request.form
    query_type = user_input.get('query_type', 'category')
    sql_files = {
        'category': '1.sql',
        'price': '2.sql'
    }
    sql_file = sql_files.get(query_type, '1.sql')
    result_info = model_route(provider, user_input, sql_file)
    if result_info.status:
        products = result_info.result
        titles = {
            'category': 'Инфомация об менеджерах',
            'price': 'Стоимсоть банкета по диапазону цен'
        }
        prod_title = titles.get(query_type, 'Результат запроса')

        if products:
            return render_template('dynamic.html', prod_title = prod_title, products = products)
        else:
            return render_template('dynamic.html', prod_title = prod_title, products = [], message = 'Ничего не найдено')
        prod_title = titles.get(query_type, 'Результат запроса')
        return render_template('dynamic.html', prod_title=prod_title, products=products)
    else:
        return 'Что-то пошло не так('
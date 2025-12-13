import json

from flask import Flask, render_template, current_app, session, redirect, url_for

from auth.access import login_required
from bp_access.access_route import blueprint_auth
from bp_query.query_route import blueprint_query
from bp_report.report_route import blueprint_reports
from bp_banquet.banquet_route import blueprint_banquet
from database.select import select_list
from database.sql_provider import SQLProvider
import os

app = Flask(__name__)
# Загружаем конфигурации из внешних JSON-файлов
with open('../data/db_config.json') as f: # Считываем файл в переменную f
    app.config['db_config'] = json.load(f) # Добавляем ключ в конфиг

with open('../data/access.json') as f:
    app.config['db_access'] = json.load(f)

app.register_blueprint(blueprint_query, url_prefix='/query')
app.register_blueprint(blueprint_auth, url_prefix='/auth')
app.register_blueprint(blueprint_reports, url_prefix='/reports')
app.register_blueprint(blueprint_banquet, url_prefix='/banquet')

app.secret_key = 'my secret key'

#для получения запросов для меню.
menu_provider = SQLProvider(os.path.join(os.path.dirname(__file__), '../bp_banquet/sql'))

@app.route('/')
def index():
    if 'user_group' in session:
        return redirect(url_for('main_menu'))

    try:
        sql_menu = menu_provider.get('get_menu.sql')
        menu_items = select_list(sql_menu, [])
    except Exception as e:
        menu_items = []
    
    return render_template('index.html', menu_items=menu_items)

@app.route('/menu')
@login_required
def main_menu():
    user_group = session.get('user_group', '')
    access_config = current_app.config['db_access']
    has_query_access = user_group in access_config and 'bp_query' in access_config[user_group] #Если группа существует, проверяет, есть ли имя нужного блюпринта
    has_report_access = user_group in access_config and 'bp_report' in access_config[user_group]
    has_banquet_access = user_group in access_config and 'bp_banquet' in access_config[user_group]
    return render_template('main_menu.html',
                           has_query_access = has_query_access,
                           has_report_access = has_report_access,
                           has_banquet_access = has_banquet_access,
                           user_group = user_group)

@app.route('/exit')
def system_exit():
    return render_template('exit.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5007, debug=True)
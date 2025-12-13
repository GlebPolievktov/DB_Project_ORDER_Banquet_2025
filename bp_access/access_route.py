import os

from flask import Blueprint, render_template, request, session, redirect

from database.sql_provider import SQLProvider
from model_route import model_route

blueprint_auth = Blueprint('bp_auth', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

@blueprint_auth.route('/', methods=['GET'])
def auth_handler():
    return render_template('auth.html')


@blueprint_auth.route('/', methods=['POST'])
def auth_form_handler():
    user_input = request.form
    result_info = model_route(provider, {'login': user_input['login']}, 'auth.sql')
    if result_info.status:
        if result_info.result[0][1] == user_input['password']: # Сравнивает пароль, полученный из БД
            session['user_group'] = result_info.result[0][2] # записывается в объект сессии
            return redirect('/')
        return render_template('auth_not.html')
    else:
        return render_template('auth_not.html')

@blueprint_auth.route('/logout')
def logout():
    session.pop('user_group', None)
    return redirect('/exit')
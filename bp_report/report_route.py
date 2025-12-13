import os
from flask import Blueprint, render_template, request, redirect, url_for

from auth.access import login_required, group_required
from database.sql_provider import SQLProvider
from model_route import model_route

blueprint_reports = Blueprint('bp_report', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

REPORT_TYPES = {
    'sell': 'реальной стоимостью банкета',
    'avance': 'плановой стоимостью банкета'
}


@blueprint_reports.route('/', methods=['GET'])
@login_required
@group_required
def report_main_menu():
    return render_template('reports_menu.html')


@blueprint_reports.route('/<report_type>', methods=['GET'])
@login_required
@group_required
def report_action_menu(report_type):
    if report_type not in REPORT_TYPES:
        return redirect(url_for('bp_report.report_main_menu'))

    report_name = REPORT_TYPES.get(report_type)
    return render_template('report_type_selection.html',
                           report_type=report_type,
                           report_name=report_name)


@blueprint_reports.route('/<report_type>/create', methods=['GET'])
@login_required
@group_required
def create_report_handle(report_type):
    if report_type not in REPORT_TYPES:
        return redirect(url_for('bp_report.report_main_menu'))

    report_type_text = 'Создание отчёта по {}'.format(REPORT_TYPES.get(report_type).lower())

    return render_template('create_report.html',
                           query_type=report_type,
                           report_type_text=report_type_text)


@blueprint_reports.route('/<report_type>/create', methods=['POST'])
@login_required
@group_required
def create_report_form(report_type):
    if report_type not in REPORT_TYPES:
        return redirect(url_for('bp_report.report_main_menu'))

    sql_files = {
        'sell': 'create_report_1.sql',
        'avance': 'create_report_2.sql'
    }
    user_input = request.form
    sql_file = sql_files.get(report_type, 'create_report_1.sql')

    report_type_text = 'Создание отчёта по {}'.format(REPORT_TYPES.get(report_type).lower())

    result_info = model_route(provider, user_input, sql_file)

    if result_info.status:
        if result_info.result:
            message = result_info.result[0][0]
        else:
            message = 'Отчёт успешно создан (процедура выполнена)'
    else:
        message = 'Ошибка создания отчёта'

    return render_template('create_report.html',
                           message=message,
                           report_type_text=report_type_text,
                           query_type=report_type)


@blueprint_reports.route('/<report_type>/show', methods=['GET'])
@login_required
@group_required
def show_report_handle(report_type):
    if report_type not in REPORT_TYPES:
        return redirect(url_for('bp_report.report_main_menu'))

    report_type_text = 'Просмотр отчётов по {}'.format(REPORT_TYPES.get(report_type).lower())

    return render_template('show_report.html',
                           query_type=report_type,
                           report_type_text=report_type_text)


@blueprint_reports.route('/<report_type>/show', methods=['POST'])
@login_required
@group_required
def show_report_form(report_type):
    if report_type not in REPORT_TYPES:
        return redirect(url_for('bp_report.report_main_menu'))

    user_input = request.form

    sql_files = {
        'sell': 'get_report_1.sql',
        'avance': 'get_report_2.sql'
    }
    sql_file = sql_files.get(report_type, 'get_report_1.sql')

    result_info = model_route(provider, user_input, sql_file)

    report_title = 'Отчёт по {}'.format(REPORT_TYPES.get(report_type).lower())

    if result_info.status:
        reports = result_info.result
        return render_template('report_result.html', report_title=report_title, reports=reports)
    else:
        report_type_text = 'Просмотр отчётов по {}'.format(REPORT_TYPES.get(report_type).lower())
        message = result_info.err_message if result_info.err_message else 'Отчёт не найден'
        return render_template('show_report.html',
                               message=message,
                               query_type=report_type,
                               report_type_text=report_type_text)
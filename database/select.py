from database.DB_context_manager import DBContextManager
from flask import current_app #global var


def select_list(_sql: str, param_list: list) -> set: # param_list список параметров
    with DBContextManager(current_app.config['db_config']) as cursor: # Параметры подключения (db_config) берутся из глобальной конфигурации Flask
        if cursor is None:
            raise ValueError('Не удалось подключиться')
        else:
            print(_sql, param_list)
            cursor.execute(_sql, param_list)
            result = cursor.fetchall() # Получение результатов
            print(result)
            return result


def select_dict(_sql, user_input: dict) -> tuple:
    user_list = []
    for key in user_input:
        user_list.append(user_input[key])
    print('user_list= in dict', user_list)
    result = select_list(_sql, user_list)
    return result
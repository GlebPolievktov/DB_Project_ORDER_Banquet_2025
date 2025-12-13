import os

class SQLProvider:

    def __init__(self, file_path):
        self.scripts = {} # Создается словарь, который будет хранить все SQL-запросы. ключ - 1.sql значение Текст SQL-запроса
        for file in os.listdir(file_path): #cyle по всем файлам
            _sql = open(f'{file_path}/{file}').read()
            self.scripts[file] = _sql

    def get(self, file): # метод извлекает текст SQL-запроса из словаря self.scripts, который был заполнен при инициализации.
        _sql = self.scripts[file]
        return _sql
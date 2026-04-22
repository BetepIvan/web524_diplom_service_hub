from django.core.management import BaseCommand
import pyodbc

from config.settings import USER, PASSWORD, HOST, DRIVER, PAD_DATABASE, DATABASE


class Command(BaseCommand):

    def handle(self, *args, **options):
        ConnectionString = f"""DRIVER={{{DRIVER}}};
                            SERVER={HOST};
                            DATABASE={PAD_DATABASE};
                            UID={USER};
                            PWD={PASSWORD};"""
        try:
            conn = pyodbc.connect(ConnectionString)
        except pyodbc.Error as err:
            print(err)
        else:
            conn.autocommit = True
            try:
                conn.execute(f'CREATE DATABASE {DATABASE};')
            except pyodbc.Error as err:
                print(f'Ошибка при создании базы данных: {err}')
            else:
                print(f'База данных {DATABASE} успешно создана')

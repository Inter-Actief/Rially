from psycopg2 import OperationalError
from django.core.management.base import BaseCommand
from django.db import connection
import time


class Command(BaseCommand):
    help = 'Blocks until database connection is valid.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print("Checking database connection . . .")
        check = False
        i = 0
        while not check:
            i += 1
            print("Checking {}...".format(i))
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                check = True
            except Exception as e:
                print(e)
                print("Can't connect to database, try again.")
                time.sleep(1)
        print("Database connection established!")
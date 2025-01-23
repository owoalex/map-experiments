import psycopg2
import os


conn_string = 'host=' + os.environ.get("POSTGRES_HOST") + ' dbname=' + os.environ.get("POSTGRES_DB") + ' user=' + os.environ.get("POSTGRES_USER") + ' password=' + os.environ.get("POSTGRES_PASSWORD") + ''

def get_postgres():
    return psycopg2.connect(conn_string)


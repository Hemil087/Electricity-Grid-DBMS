import psycopg2

DB_CONFIG={
    "host": "localhost",
    "port": 5432,
    "dbname": "electricity_grid",
    "user": "grid_admin",
    "password": "grid_pass",
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)
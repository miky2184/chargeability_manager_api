from psycopg2._psycopg import connection
import psycopg2


def get_conn(db_host: str, db_name: str, db_user: str, db_pwd: str, db_port: str) -> connection:
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pwd,
        port=db_port,
        application_name="fin-api"
    )

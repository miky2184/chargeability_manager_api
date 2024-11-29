from distutils.command.config import config

from psycopg2._psycopg import connection
import psycopg2
from typing import Optional
from core.auth_config import *
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_conn(db_host: str, db_name: str, db_user: str, db_pwd: str, db_port: str) -> connection:
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pwd,
        port=db_port,
        application_name="fin-api"
    )

def get_user_by_username(conn: connection, username: str) -> Optional[dict]:
    query = "SELECT * FROM chargeability_manager.users WHERE username = %s"
    with conn.cursor() as cur:
        cur.execute(query, (username,))
        user = cur.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "hashed_password": user[3],
                "full_name": user[4],
                "disabled": user[5],
            }
    return None

def create_user(conn: connection, username: str, email: str, hashed_password: str, full_name: Optional[str]):
    query = """
    INSERT INTO chargeability_manager.users (username, email, hashed_password, full_name)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """
    with conn.cursor() as cur:
        cur.execute(query, (username, email, hashed_password, full_name))
        conn.commit()
        return cur.fetchone()[0]

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    conn = get_conn(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PWD, Config.DB_PORT)
    user = get_user_by_username(conn, username)
    if user is None:
        raise credentials_exception
    return user
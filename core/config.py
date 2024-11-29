import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PWD = os.getenv("DB_PWD")
    DB_PORT = os.getenv("DB_PORT")
    LOG_PATH = os.getenv("LOG_PATH")
    LOG_LEVEL = os.getenv("LOG_LEVEL")
    SECRETKEY = os.getenv("SECRETKEY")
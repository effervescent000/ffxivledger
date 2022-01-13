"""Flask configuration variables."""
import os
from datetime import timedelta


class Config:
    """Set Flask configuration from .env file."""

    # General Config
    SECRET_KEY = os.environ['SECRET_KEY']
    XIVAPI_KEY = os.environ['XIVAPI_KEY']
    

    # Database
    # SQLALCHEMY_DATABASE_URI = "sqlite:///ffxivledger.sqlite"
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'].replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #JWT config
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = True
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    JWT_SESSION_COOKIE = False
    JWT_COOKIE_DOMAIN = "127.0.0.1:3000"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=6)
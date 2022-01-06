"""Flask configuration variables."""
import os


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

    # praetorian config
    JWT_ACCESS_LIFESPAN = {"hours": 24}
    JWT_REFRESH_LIFESPAN = {"days": 30}

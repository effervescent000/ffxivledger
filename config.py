"""Flask configuration variables."""
import os
from boto.s3.connection import S3Connection


class Config:
    """Set Flask configuration from .env file."""

    # General Config
    SECRET_KEY = S3Connection(os.environ('SECRET_KEY'))
    XIVAPI_KEY = S3Connection(os.environ('XIVAPI_KEY'))
    

    # Database
    SQLALCHEMY_DATABASE_URI = "sqlite:///ffxivledger.sqlite"
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # praetorian config
    JWT_ACCESS_LIFESPAN = {"hours": 24}
    JWT_REFRESH_LIFESPAN = {"days": 30}

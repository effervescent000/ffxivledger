"""Flask configuration variables."""
import os


class Config:
    """Set Flask configuration from .env file."""

    # General Config
    SECRET_KEY = os.environ['SECRET_KEY']
    XIVAPI_KEY = os.environ['XIVAPI_KEY']
    

    # Database
    # SQLALCHEMY_DATABASE_URI = "sqlite:///ffxivledger.sqlite"
    SQLALCHEMY_DATABASE_URI = "postgresql://orjrxltdmizsdq:d716f0c782db410f2ef6a29a5f9969b13cf56bceac6b442081aa37fcad33ba43@ec2-54-90-211-192.compute-1.amazonaws.com:5432/deq71c168lhqov"
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # praetorian config
    JWT_ACCESS_LIFESPAN = {"hours": 24}
    JWT_REFRESH_LIFESPAN = {"days": 30}

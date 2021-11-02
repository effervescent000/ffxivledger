from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import LoginManager
from .models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

login_manager = LoginManager()


def config_login_manager(app):
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

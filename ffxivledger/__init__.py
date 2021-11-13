import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_object('config.Config')
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():

        from .models import User, Item, Transaction, Stock, Product, Recipe, Component
        db.create_all()

        from . import auth
        app.register_blueprint(auth.bp)

        from . import dashboard
        app.register_blueprint(dashboard.bp)
        app.add_url_rule('/', endpoint='index')

        from . import item
        app.register_blueprint(item.bp)

        from . import recipe
        app.register_blueprint(recipe.bp)

        from . import transaction
        app.register_blueprint(transaction.bp)

        return app

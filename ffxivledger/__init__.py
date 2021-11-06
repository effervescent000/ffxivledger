import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_debugtoolbar import DebugToolbarExtension

db = SQLAlchemy()
# toolbar = DebugToolbarExtension()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_object('config.Config')
    else:
        app.config.from_mapping(test_config)

    # toolbar.init_app(app)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    with app.app_context():

        from . import auth
        app.register_blueprint(auth.bp)
        auth.config_login_manager(app)

        from .models import User, Item, Price, Stock, Product, Recipe, Component
        db.create_all()

        from . import dashboard
        app.register_blueprint(dashboard.bp)
        app.add_url_rule('/', endpoint='index')

        from . import item
        app.register_blueprint(item.bp)

        from . import recipe
        app.register_blueprint(recipe.bp)

        return app

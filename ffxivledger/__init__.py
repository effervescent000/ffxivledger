import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

db = SQLAlchemy()
ma = Marshmallow()
cors = CORS()
jwt = JWTManager()

load_dotenv()

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

    cors.init_app(app, supports_credentials=True)
    db.init_app(app)
    # login_manager.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    

    with app.app_context():

        from .models import User, Profile, Retainer, Item, Transaction, Stock, Recipe, Component, World, Datacenter, ItemStats
        db.create_all()
        # from .models import User
        # guard.init_app(app, User)

        from . import auth
        app.register_blueprint(auth.bp)

        # from . import dashboard
        # app.register_blueprint(dashboard.bp)
        # app.add_url_rule('/', endpoint='index')

        from . import item
        app.register_blueprint(item.bp)

        from . import recipe
        app.register_blueprint(recipe.bp)

        from . import transaction
        app.register_blueprint(transaction.bp)

        from . import crafting_calc
        app.register_blueprint(crafting_calc.bp)

        from . import profile
        app.register_blueprint(profile.bp)

        from . import world
        app.register_blueprint(world.bp)

        return app

from ffxivledger import create_app
app = create_app()
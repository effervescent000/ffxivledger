import functools
import pytest
import datetime
from flask_login import login_user

from ffxivledger import create_app
from ffxivledger import db
from ffxivledger.models import Item, Price, Stock, Recipe, Product, Component, User
from ffxivledger.utils import get_item

TEST_DATABASE_URI = 'sqlite:///test_database.sqlite'


@pytest.fixture
def app():
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'dev',
        'WTF_CSRF_ENABLED': False,
        'WTF_CSRF_CHECK_DEFAULT': False,
        'WTF_CSRF_METHODS': [],
        'LOGIN_DISABLED': True
    }
    app = create_app(settings_override)

    with app.app_context():
        db.init_app(app)

        populate_test_data()

        yield app

        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def populate_test_data():
    user_list = [
        User(username='Admin', role='admin'),
        User(username='super_user', role='super_user'),
        User(username='test_user')
    ]
    for x in user_list:
        x.set_password('test_password')
        db.session.add(x)
    db.session.commit()

    new_items = [
        Item(name='Test item', value='test_item', type='product'),
        Item(name="Patrician's Bottoms", value='patricians_bottoms', type='product'),
        Item(name='third test item', value='third_test_item', type='material'),
        Item(name='test bolts of cloth', value='test_bolts_of_cloth', type='intermediate')
    ]
    for x in new_items:
        db.session.add(x)
    db.session.commit()

    # add some stock of each item into the inventory for each user
    for x in user_list:
        Item.query.get(new_items[0].value).adjust_stock(3, x.id)
        Item.query.get(new_items[1].value).adjust_stock(0, x.id)
        Item.query.get(new_items[2].value).adjust_stock(300, x.id)
        Item.query.get(new_items[3].value).adjust_stock(20, x.id)

    get_item(new_items[0].value).process_transaction(price_input=50000, time=datetime.datetime.now(), amount=-1, user_id=1)
    get_item(new_items[3].value).process_transaction(price_input=-200, time=datetime.datetime.now(), amount=30, user_id=1)
    # new_prices = [
    #     Price(price_input=50000, price_time=datetime.datetime.now(), amount=-1, item_value=new_items[0].value, user_id=1),
    #     Price(price_input=-200, price_time=datetime.datetime.now(), amount=30, item_value=new_items[3].value, user_id=1)
    # ]
    # for x in new_prices:
    #     db.session.add(x)
    # db.session.commit()

    # for i in range(len(new_prices) - 1):
    #     price = new_prices[i]
    #     Item.query.get(price.item_value).adjust_stock(price.amount, price.user_id)
    # db.session.commit()

    # at this point what I expect to have in stock is:
    # Test Item 2, patrician's bottoms 0, third test item 300, test bolts of cloth 50

    new_recipes = [
        Recipe(job='WVR', id=1),  # patrician's bottoms
        Recipe(job='GSM', id=2)  # test item
    ]
    for x in new_recipes:
        db.session.add(x)
    db.session.commit()
    new_products = [
        Product(item_value='patricians_bottoms', item_quantity=1, recipe_id=1),
        Product(item_value='test_item', item_quantity=1, recipe_id=2)
    ]
    for x in new_products:
        db.session.add(x)
    db.session.commit()
    new_components = [
        Component(item_value='test_bolts_of_cloth', item_quantity=5, recipe_id=1),
        Component(item_value='test_bolts_of_cloth', item_quantity=2, recipe_id=1),
        Component(item_value='third_test_item', item_quantity=1, recipe_id=1)
    ]
    # right now test_item has NO components and I'm leaving it like this for testing purposes
    for x in new_components:
        db.session.add(x)
    db.session.commit()

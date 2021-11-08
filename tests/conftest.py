import os
import pytest
import tempfile
import datetime

from ffxivledger import create_app
from ffxivledger import db
from ffxivledger.models import Item, Price, User
from ffxivledger.utils import name_to_value

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
        'WTF_CSRF_METHODS': []
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
    new_items = [
        Item(name='Test item', value='test_item', type='product'),
        Item(name="Patrician's Bottoms", value='patricians_bottoms', type='product'),
        Item(name='third test item', value='third_test_item', type='material'),
        Item(name='test bolts of cloth', value='test_bolts_of_cloth', type='intermediate')
    ]
    for x in new_items:
        db.session.add(x)
    db.session.commit()

    # add some stock of each item into our inventory
    Item.query.get(new_items[0].value).adjust_stock(3)
    Item.query.get(new_items[1].value).adjust_stock(0)
    Item.query.get(new_items[2].value).adjust_stock(300)
    Item.query.get(new_items[3].value).adjust_stock(20)

    new_prices = [
        Price(price_input=50000, price_time=datetime.datetime.now(), amount=-1, item_value=new_items[0].value),
        Price(price_input=-200, price_time=datetime.datetime.now(), amount=30, item_value=new_items[3].value)
    ]
    for x in new_prices:
        db.session.add(x)
    db.session.commit()

    Item.query.get(new_prices[0].item_value).adjust_stock(new_prices[0].amount)
    Item.query.get(new_prices[1].item_value).adjust_stock(new_prices[1].amount)
    db.session.commit()

    # at this point what I expect to have in stock is:
    # Test Item 2, patrician's bottoms 0, third test item 300, test bolts of cloth 50

    user = User()
    user.name = 'Admin'
    user.set_password('password')
    db.session.add(user)
    db.session.commit()

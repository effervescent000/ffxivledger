import pytest
from wtforms import ValidationError

from ffxivledger.models import Item, Transaction, Stock


def test_dashboard(client):
    # first, make sure the page loads successfully
    assert client.get('/').status_code == 200

    # now ensure the data in the database (based on the test data in conftest.py) is correct
    assert Item.query.get('test_item').type == 'product'
    assert Transaction.query.get(13).gil_value == 50000
    assert Stock.query.get(1).amount == 2

@pytest.mark.parametrize(('item_value', 'amount', 'gil_value', 'new_stock'), (
        ('test_item', 1, 20000, 1),
        ('third_test_item', 100, 300, 300)
))
def test_add_sale(client, item_value, amount, gil_value, new_stock):
    old_amount = Stock.query.filter_by(item_value=item_value, user_id=1).one_or_none().amount
    data = {'item': item_value, 'amount': amount, 'gil_value': gil_value, 'sale_button': True}
    client.post('/', data=data)

    assert old_amount - amount == new_stock


@pytest.mark.parametrize(('item_value', 'amount', 'gil_value'), (
        ('test_item', None, 20000),
        ('third_test_item', 100, None)
))
def test_add_sale_validation(client, item_value, amount, gil_value):
    with pytest.raises(ValidationError):
        data = {'item': item_value, 'amount': amount,
                'gil_value': gil_value, 'sale_button': True}
        client.post('/', data=data)


@pytest.mark.parametrize(('item_value', 'amount', 'gil_value', 'new_stock'), (
        ('test_bolts_of_cloth', 100, 100, 150),
        ('third_test_item', 50, 200, 450)
))
def test_add_purchase(client, item_value, amount, gil_value, new_stock):
    old_amount = Stock.query.filter_by(item_value=item_value, user_id=1).one_or_none().amount
    data = {'item': item_value, 'amount': amount,'gil_value': gil_value, 'purchase_button': True}
    client.post('/', data=data)

    assert old_amount + amount == new_stock


@pytest.mark.parametrize('item_value', (
        'test_item',
        'test_bolts_of_cloth'
))
def test_view_data(client, item_value):
    data = {'item': item_value, 'view_button': True}
    response = client.post('/', data=data)

    assert response.status_code == 302

@pytest.mark.parametrize(('item_value', 'amount', 'expected_amount'), (
        ('test_item', 1, 3),
        ('patricians_bottoms', 5, 5)
))
def test_add_stock_button(client, item_value, amount, expected_amount):
    data = {'item': item_value, 'amount': amount, 'add_stock_button': True}
    client.post('/', data=data)

    assert Stock.query.filter_by(item_value=item_value,user_id=1).one_or_none().amount == expected_amount


@pytest.mark.parametrize(('item_value', 'amount', 'expected_amount'), (
        ('test_item', 1, 1),  # (2-1)
        # this should go below zero and then be set to 0 (0-3)
        ('patricians_bottoms', 3, 0),
        ('test_item', 2, 0)  # this should end up at zero exactly (2-2)
))
def test_remove_stock_button(client, item_value, amount, expected_amount):
    data = {'item': item_value, 'amount': amount, 'remove_stock_button': True}
    client.post('/', data=data)
    assert Stock.query.filter_by(item_value=item_value,user_id=1).one_or_none().amount == expected_amount

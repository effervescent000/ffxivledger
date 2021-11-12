import pytest

from ffxivledger.models import Price


@pytest.mark.parametrize('id', [
    1,
    2
])
def test_view_price(client, id):
    # TODO incorporate user-checking
    response = client.get('price/{}'.format(id))

    assert response.status_code == 200


@pytest.mark.parametrize('id,item_value,price_input,price_time,amount,user_id', [
    (1, 'patricians_bottoms', 40000, '2021-8-9 5:29', -2, 1)
])
def test_edit_price(client, id, item_value, price_input, price_time, amount, user_id):
    data = {
        'item_value': item_value,
        'price_input': price_input,
        'price_time': price_time,
        'item_quantity': amount
    }

    price = Price.query.get(id)

    response = client.post('price/{}'.format(id), data=data)
    assert price.item_value == item_value
    assert price.amount == amount

    
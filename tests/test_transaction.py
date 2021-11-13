import pytest

from ffxivledger.models import Transaction


@pytest.mark.parametrize('id', [
    1,
    2
])
def test_view_transaction(client, id):
    # TODO incorporate user-checking
    response = client.get('transaction/{}'.format(id))

    assert response.status_code == 200


@pytest.mark.parametrize('id,item_value,gil_value,time,amount,user_id', [
    (1, 'patricians_bottoms', 40000, '2021-8-9 5:29', -2, 1)
])
def test_edit_transaction(client, id, item_value, gil_value, time, amount, user_id):
    data = {
        'item_value': item_value,
        'gil_value': gil_value,
        'time': time,
        'item_quantity': amount
    }

    price = Transaction.query.get(id)

    client.post('transaction/{}'.format(id), data=data)
    assert price.item_value == item_value
    assert price.amount == amount

    
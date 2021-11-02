import pytest

from ffxivledger.models import Item
from ffxivledger.utils import name_to_value


@pytest.mark.parametrize(('item_name', 'item_type', 'expected_value'), (
        ('Yet Another test item', 'product', 'yet_another_test_item'),
        ('An invalid test item', '', 'an_invalid_test_item')
))
def test_create_item(client, item_name, item_type, expected_value):
    # first make sure page loads successfully
    assert client.get('item/edit/new').status_code == 200

    # now add an item
    data = {'item_name': item_name, 'item_value': name_to_value(item_name)}
    client.post('item/edit/new', data=data)

    # check to see if the items were entered successfully
    assert Item.query.get(expected_value).one_or_none() is not None

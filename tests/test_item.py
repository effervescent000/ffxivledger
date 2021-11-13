import pytest

from ffxivledger.models import Item
from ffxivledger.utils import get_item, name_to_value


@pytest.mark.parametrize('item_value', [
    'test_item', 'patricians_bottoms'
])
def test_view_item(client, item_value):
    rv = client.get('item/view/{}'.format(item_value))
    item = get_item(item_value)

    # did it load successfully?
    assert b'Gil' in rv.data


@pytest.mark.parametrize(('item_name', 'item_type', 'expected_value'), (
        ('Yet Another test item', 'product', 'yet_another_test_item'),
        ('An invalid test item', '', 'an_invalid_test_item')
))
def test_create_item(client, item_name, item_type, expected_value):
    # first make sure page loads successfully
    assert client.get('item/edit/new').status_code == 200

    # now add an item
    data = {'item_name': item_name, 'item_value': name_to_value(item_name), 'item_type': item_type}
    client.post('item/edit/new', data=data)

    # check to see if the items were entered successfully
    assert Item.query.get(expected_value) is not None

@pytest.mark.parametrize('item_value,new_name,new_type', [
    ('test_item', 'New Test Item', 'material')
])
def test_edit_item(client, item_value, new_name, new_type):
    item_old_name = get_item(item_value).name
    data = {'item_name': new_name, 'item_type': new_type}

    client.post('item/edit/{}'.format(item_value), data=data)
    assert get_item(name_to_value(new_name)).name == new_name

@pytest.mark.parametrize('item_value', [
    'test_item', # a valid item
    'not_a_valid_item' # what it says
])
def test_delete_item(client, item_value):
    client.post('item/delete/{}'.format(item_value))
    assert Item.query.get(item_value) is None
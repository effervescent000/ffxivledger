import random

import pytest

from ffxivledger.models import Recipe, Product, Component


@pytest.mark.parametrize('product,product_quantity,job,components_dict', [
    ('test_item', 1, 'GSM', {
        'line_item_list-0-item_value': 'third_test_item',
        'line_item_list-0-item_quantity': 2,
        'line_item_list-1-item_value': 'test_bolts_of_cloth',
        'line_item_list-1-item_quantity': 5
    })
])
def test_create_recipe(client, product, product_quantity, job, components_dict):
    current_recipes = len(Recipe.query.all())
    current_components = len(Component.query.all())

    data = {
        'product_name': product, 'product_quantity': product_quantity, 'job_field': job
    }
    for k, v in components_dict.items():
        data[k] = v
    client.post('recipe/edit/new', data=data)

    assert len(Recipe.query.all()) == current_recipes + 1
    assert len(Component.query.all()) == current_components + len(components_dict) / 2

    # test some random entries for validity
    i = random.randint(1, len(Recipe.query.all()))
    assert Recipe.query.get(i).product.item_value is not None

from werkzeug.exceptions import abort

from .models import Item


def get_item(value):
    """Returns the product specified by the value (or throws a 404 error if no product is found)"""
    item = Item.query.get(value)
    if item is None:
        print(value)
        abort(404)
    return item


def name_to_value(name):
    value = name
    value = value.replace(' ', '_')
    value = value.replace("'", '')
    value = value.lower()
    return value


def get_item_options():
    item_options = []
    for x in Item.query.all():
        item_options.append((x.value, x.name))
    return item_options


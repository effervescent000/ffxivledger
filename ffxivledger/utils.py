import functools
from werkzeug.exceptions import abort
from flask_login import current_user

from .models import Item, User


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
    item_options = [('', '---')]
    for x in Item.query.all():
        item_options.append((x.value, x.name))
    return item_options


def get_craftables_options():
    item_options = []
    for x in Item.query.all():
        if x.type != 'material':
            item_options.append((x.value, x.name))
    return item_options


def admin_required(func):
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        # I don't know if this will work
        if current_user.role != 'admin':
            abort(401)
        return func(*args, **kwargs)
    return decorated_view
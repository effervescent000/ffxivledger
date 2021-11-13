import functools
from werkzeug.exceptions import abort
from flask_login import current_user
from flask import current_app
from datetime import datetime

from . import db

from .models import Item, User, Transaction, Component, Stock, Product, time_format


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
    item_options = [('', '---')]
    for x in Item.query.all():
        if x.type != 'material':
            item_options.append((x.value, x.name))
    return item_options


def admin_required(func):
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.config.get('TESTING') is False:
            if current_user.role != 'admin':
                abort(401)
            return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    return decorated_view


def rename_item(item, new_name):
    if new_name == '':
        pass
    else:
        old_value = item.value
        item.name = new_name
        item.value = name_to_value(new_name)
        for x in Transaction.query.filter_by(item_value=old_value).all():
            x.item_value = item.value
        for x in Stock.query.filter_by(item_value=old_value).all():
            x.item_value = item.value
        for x in Component.query.filter_by(item_value=old_value).all():
            x.item_value = item.value
        for x in Product.query.filter_by(item_value=old_value).all():
            x.item_value = item.value
        db.session.commit()


def convert_to_time_format(time):
    """Convert a datetime object into a string in the preferred time format"""
    new_time = time.strftime(time_format)
    # new_time = datetime.strptime(new_time, time_format)
    return new_time
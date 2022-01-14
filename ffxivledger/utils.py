import functools
from werkzeug.exceptions import abort
from flask_jwt_extended import current_user
from flask import current_app
from datetime import datetime

from .models import Item, time_format


def get_item_options():
    item_options = [("", "---")]
    for x in Item.query.all():
        item_options.append((str(x.id), x.name))
    item_options.sort(key=lambda x: x[1])
    return item_options


def get_craftables_options():
    item_options = [("", "---")]
    for x in Item.query.all():
        if len(x.recipes) > 0:
            item_options.append((str(x.id), x.name))
    item_options.sort(key=lambda x: x[1])
    return item_options


def admin_required(func):
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_app.config.get("TESTING"):
            if current_user.roles != "admin":
                abort(401)
            return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return decorated_view


def convert_to_time_format(time):
    """Convert a datetime object into a string in the preferred time format"""
    return time.strftime(time_format)


def convert_string_to_datetime(time):
    if time == None:
        return datetime.min
    return datetime.strptime(time, time_format)

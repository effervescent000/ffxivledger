import datetime
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, current_app
)
from flask_login import current_user

from wtforms import ValidationError

from . import db
from .models import Item, Transaction, Stock
from .forms import DashboardForm
from .utils import get_item, get_item_options, convert_to_time_format

bp = Blueprint('dashboard', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    form = DashboardForm()
    if form.validate_on_submit():
        print('Made it through validation!')
        # first collect info from form
        item_value = form.item.data
        time = convert_to_time_format(datetime.datetime.now())
        gil_value = form.gil_value.data
        amount = form.amount.data

        # reject immediately if an item was not selected
        if item_value == '':
            raise ValidationError('Select an item')
        else:
            user_id = None
            if current_app.config.get('TESTING') is True:
                user_id = 1
            else:
                user_id = current_user.id
            # check which button was clicked
            if form.sale_button.data or form.remove_stock_button.data:
                # make sale amounts negative
                amount *= -1

                if form.sale_button.data:
                    get_item(item_value).process_transaction(gil_value, time, amount, user_id)
                else:
                    Item.query.get(item_value).adjust_stock(amount, user_id)
                return redirect(url_for('dashboard.index'))
            elif form.view_button.data:
                return redirect(url_for('item.view_item', value=item_value))
            elif form.purchase_button.data:
                # make prices negative for purchases
                gil_value *= -1
                get_item(item_value).process_transaction(gil_value, time, amount, user_id)
                return redirect(url_for('dashboard.index'))
            elif form.add_stock_button.data:
                Item.query.get(item_value).adjust_stock(amount, user_id)
                return redirect(url_for('dashboard.index'))
            elif form.create_recipe_button.data:
                # TODO figure out why this is sending a None for product?
                return redirect(url_for('recipe.create_recipe'))
            elif form.view_recipes_button.data:
                return redirect(url_for('recipe.view_recipes', value=item_value))
            else:
                return "Somehow some other button was pressed on the dashboard ???"
    form.item.choices = get_item_options()
    stock_list = get_stock_list()
    return render_template('ffxivledger/index.html', stock_list=stock_list, form=form)


def get_stock_list():
    stock_query = Stock.query.filter(Stock.amount >= 1).all()
    stock_list = [x for x in stock_query if x.item.type == 'product']
    return stock_list

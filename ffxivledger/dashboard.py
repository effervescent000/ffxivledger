import datetime
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from . import db
from .models import Item, Price, Stock
from .forms import DashboardForm
from .utils import get_item_options

bp = Blueprint('dashboard', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    form = DashboardForm()
    if request.method == 'POST':
        # first collect info from form
        item_value = form.item.data
        time = datetime.datetime.now()
        price_input = form.price.data
        amount = form.amount.data

        if amount is None:
            amount = 1

        # check which button was clicked
        if form.sale_button.data:
            # make sale amounts negative
            amount *= -1

            process_transaction(price_input, time, amount, item_value)

            return redirect(url_for('dashboard.index'))
        elif form.view_button.data:
            return redirect(url_for('item.view_item', value=item_value))
        elif form.purchase_button.data:
            # make prices negative for purchases
            price_input *= -1

            process_transaction(price_input, time, amount, item_value)

            return redirect(url_for('dashboard.index'))
        else:
            return "Somehow some other button was pressed on the dashboard ???"
    form.item.choices = get_item_options()
    stock_list = get_stock_list()
    return render_template(
        'ffxivledger/index.html',
        stock_list=stock_list,
        form=form
    )


def process_transaction(price_input, time, amount, item_value):
    price = Price(
        price_input=price_input,
        price_time=time,
        amount=amount,
        item_value=item_value
    )
    db.session.add(price)
    db.session.commit()
    # now adjust the amount stored in the stock table
    Item.query.get(item_value).adjust_stock(amount)


def get_stock_list():
    # TODO make it so this only shows products (right now it will include materials)
    stock_list = Stock.query.filter(Stock.amount >= 1).all()
    return stock_list

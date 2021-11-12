from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import login_required

from .models import Item, Price
from . import db
from .forms import PriceForm

bp = Blueprint('price', __name__, url_prefix='/price')

@bp.route('/<id>', methods=('GET', 'POST'))
@login_required
def view_price(id):
    # TODO make it so this checks users (so people can only see their own prices)
    price = Price.query.get(id)
    if request.method == 'POST':
        form = PriceForm()
        item_value = form.item_value.data
        price_input = form.price_input.data
        item_quantity = form.item_quantity.data
        price_time = form.price_time.data

        if price.item_value != item_value:
            price.item_value = item_value
        if price.price_input != price_input:
            price.price_input = price_input
        if price.amount != item_quantity:
            price.amount = item_quantity
        if price.price_time != price_time:
            price.price_time = price_time
        db.session.commit()
    form = PriceForm(item_value=price.item_value,price_input=price.price_input,item_quantity=price.amount,price_time=price.price_time)
    return render_template('ffxivledger/price_view.html', form=form)


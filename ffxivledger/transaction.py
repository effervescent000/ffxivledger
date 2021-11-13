from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import login_required

from .models import Item, Transaction
from . import db
from .forms import TransactionForm

bp = Blueprint('transaction', __name__, url_prefix='/transaction')

@bp.route('/<id>', methods=('GET', 'POST'))
@login_required
def view_transaction(id):
    # TODO make it so this checks users (so people can only see their own prices)
    transaction = Transaction.query.get(id)
    if request.method == 'POST':
        form = TransactionForm()
        item_value = form.item_value.data
        gil_value = form.gil_value.data
        item_quantity = form.item_quantity.data
        time = form.time.data

        if transaction.item_value != item_value:
            transaction.item_value = item_value
        if transaction.gil_value != gil_value:
            transaction.gil_value = gil_value
        if transaction.amount != item_quantity:
            transaction.amount = item_quantity
        if transaction.time != time:
            transaction.time = time
        db.session.commit()
    form = TransactionForm(item_value=transaction.item_value,gil_value=transaction.gil_value,item_quantity=transaction.amount,time=transaction.time)
    return render_template('ffxivledger/price_view.html', form=form)


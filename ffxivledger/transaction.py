from datetime import datetime
from flask import Blueprint, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user

from .models import Transaction, Item
from . import db
from .forms import TransactionForm
from .utils import convert_to_time_format
from .schema import TransactionSchema

bp = Blueprint("transaction", __name__, url_prefix="/transaction")

one_transaction_schema = TransactionSchema()
multi_transaction_schema = TransactionSchema(many=True)


@bp.route("/view/<id>", methods=("GET", "POST"))
@login_required
def view_transaction(id):
    # TODO make it so this checks users (so people can only see their own prices)
    transaction = Transaction.query.get(id)
    if request.method == "POST":
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
    form = TransactionForm(
        item_value=transaction.item_value,
        gil_value=transaction.gil_value,
        item_quantity=transaction.amount,
        time=transaction.time,
    )
    return render_template("ffxivledger/price_view.html", form=form)


@bp.route("/get/<id>", methods=["GET"])
def get_transaction_by_id(id):
    return jsonify(one_transaction_schema.dump(Transaction.query.get(id)))


@bp.route("/get/item/<item_value>", methods=["GET"])
def get_transactions_by_item(item_value):
    user_id = current_user.id
    return jsonify(
        multi_transaction_schema.dump(Transaction.query.filter_by(item_value=item_value, user_id=user_id).all())
    )


@bp.route("/add", methods=["POST"])
def add_transaction():
    data = request.get_json()
    item_value = data.get("item_value")
    user_id = current_user.id
    amount = data.get("amount")
    gil_value = data.get("gil_value")
    time = data.get("time")

    if item_value == None:
        return jsonify("Must include an item value")
    if user_id == None:
        return jsonify("Must include a user")
    if time == None:
        time = convert_to_time_format(datetime.now())
    else:
        # TODO figure out how JS passes this and convert it appropriately
        pass

    item = Item.query.get(item_value)
    transaction = None
    if item != None:
        transaction = item.process_transaction(gil_value=gil_value, time=time, amount=amount, user_id=user_id)
    return jsonify(one_transaction_schema.dump(transaction))

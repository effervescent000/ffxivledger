from datetime import datetime
from flask import Blueprint, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
import flask_praetorian as fp

from .models import Transaction, Item
from . import db
# from .forms import TransactionForm
from .utils import convert_to_time_format
from .schema import TransactionSchema

bp = Blueprint("transaction", __name__, url_prefix="/transaction")

one_transaction_schema = TransactionSchema()
multi_transaction_schema = TransactionSchema(many=True)


@bp.route("/get/<id>", methods=["GET"])
def get_transaction_by_id(id):
    return jsonify(one_transaction_schema.dump(Transaction.query.get(id)))


@bp.route("/get/item/<item_value>", methods=["GET"])
@fp.auth_required
def get_transactions_by_item(item_value):
    user_id = fp.current_user().id
    return jsonify(
        multi_transaction_schema.dump(Transaction.query.filter_by(item_value=item_value, user_id=user_id).all())
    )


@bp.route("/add", methods=["POST"])
@fp.auth_required
def add_transaction():
    data = request.get_json()
    item_id = int(data.get("item_id"))
    profile = fp.current_user().get_active_profile()
    amount = data.get("amount")
    gil_value = data.get("gil_value")
    time = data.get("time")

    if item_id == None:
        return jsonify("Must include an item id")
    if time == None:
        time = convert_to_time_format(datetime.now())
    else:
        # TODO figure out how JS passes this and convert it appropriately
        pass

    item = Item.query.get(item_id)
    transaction = None
    if item != None:
        transaction = item.process_transaction(gil_value=gil_value, time=time, amount=amount, profile_id=profile.id)
    return jsonify(one_transaction_schema.dump(transaction))

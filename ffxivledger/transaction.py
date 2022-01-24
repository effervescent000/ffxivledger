from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, current_user

from .models import Transaction, Item
from .utils import convert_to_time_format
from .schema import TransactionSchema

bp = Blueprint("transaction", __name__, url_prefix="/transaction")

one_transaction_schema = TransactionSchema()
multi_transaction_schema = TransactionSchema(many=True)


@bp.route("/get/<id>", methods=["GET"])
def get_transaction_by_id(id):
    return jsonify(one_transaction_schema.dump(Transaction.query.get(id)))


@bp.route("/get/item/<item_id>", methods=["GET"])
@jwt_required()
def get_transactions_by_item(item_id):
    profile = current_user.get_active_profile()
    return jsonify(
        multi_transaction_schema.dump(Transaction.query.filter_by(item_id=item_id, profile_id=profile.id).all())
    )


@bp.route("/add", methods=["POST"])
@jwt_required()
def add_transaction():
    data = request.get_json()
    item_id = int(data.get("item_id"))
    profile = current_user.get_active_profile()
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

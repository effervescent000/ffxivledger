from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import flask_praetorian as fp

import requests as req

from ffxivledger.utils import convert_to_time_format

from .models import Item, Transaction, Stock, Skip
from .schema import ItemSchema, StockSchema, TransactionSchema, SkipSchema
from . import db

bp = Blueprint("item", __name__, url_prefix="/item")
one_item_schema = ItemSchema()
multi_item_schema = ItemSchema(many=True)
multi_transaction_schema = TransactionSchema(many=True)
multi_stock_schema = StockSchema(many=True)
one_skip_schema = SkipSchema()
multi_skip_schema = SkipSchema(many=True)


@bp.route("/get/<id>", methods=["GET"])
def get_item_by_id(id):
    item = Item.query.get(id)
    return jsonify(one_item_schema.dump(item))


@bp.route("/get_name/<name>", methods=["GET"])
def get_item_by_name(name):
    item = Item.query.filter_by(name=name).first()
    return jsonify(one_item_schema.dump(item))


@bp.route("/view/<value>/sales", methods=["GET"])
def get_item_sales(value):
    sales_list = Transaction.query.filter(Transaction.item_value == value, Transaction.gil_value > 0).all()
    return jsonify(multi_transaction_schema.dump(sales_list))


@bp.route("/view/<value>/purchases", methods=["GET"])
def get_item_purchases(value):
    purchases_list = Transaction.query.filter(Transaction.item_value == value, Transaction.gil_value < 0).all()
    return jsonify(multi_transaction_schema.dump(purchases_list))


@bp.route("/stock", methods=["GET"])
@fp.auth_required
def get_stock_list():
    profile = fp.current_user().get_active_profile()
    stock_list = Stock.query.filter(Stock.profile_id == profile.id, Stock.amount > 0).all()
    if stock_list != None:
        return jsonify(multi_stock_schema.dump(stock_list))
    else:
        return jsonify([])


@bp.route("/get/all", methods=["GET"])
def get_all_items():
    return jsonify(multi_item_schema.dump(Item.query.all()))



@bp.route("/add", methods=["POST"])
def create_item():
    return jsonify(one_item_schema.dump(process_item(request.get_json())))


@bp.route("/add/many", methods=["POST"])
def create_multiple_items_from_dump():
    items_list = []
    data = request.get_json()
    for item in data:
        items_list.append(process_item(item))
    return jsonify(multi_item_schema.dump(items_list))


@bp.route("/add/search", methods=['POST'])
def create_multiple_items_from_search():
    data = request.get_json()
    items_list = []
    name = data.get("name")
    search = req.get(
        f'https://xivapi.com/search?indexes=Item&string={name}&private_key={current_app.config.get("XIVAPI_KEY")}'
    ).json()
    results = search.get("Results")
    for result in results:
        result_name = result.get("Name")
        if result_name.startswith(name):
            items_list.append(process_item({"name": result_name}))
    return jsonify(multi_item_schema.dump(items_list))


def process_item(data):
    name = data.get("name")
    # GET request to xivapi to search for the item
    search = req.get(
        f'https://xivapi.com/search?indexes=Item&string={name}&private_key={current_app.config.get("XIVAPI_KEY")}'
    ).json()
    # iterate through results (ideally only 1 result) for an exact name much (with .lower() run)
    results = search.get("Results")
    item_id = None
    if len(results) > 1:
        for result in results:
            if name.lower() == result.get("Name").lower():
                item_id = result.get("ID")
    elif len(results) == 1:
        item_id = results[0].get("ID")
    else:
        # if no match is found, then return error
        return jsonify("No results found in XIVAPI search")
    
    item = Item.query.get(item_id)
    if item == None:
        # GET request to xivapi again for the item id
        item_data = req.get(f"https://xivapi.com/Item/{item_id}").json()
        # populate item's data from the return JSON
        item = Item(name=item_data.get("Name"), id=item_id)
        db.session.add(item)
        db.session.commit()
        # if any recipes are found, then query them as well and repeat the process
        recipes = item_data.get("Recipes")
        if recipes != None and len(recipes) > 0:
            for recipe in recipes:
                data = {"id": recipe.get("ID")}
                req.post("http://127.0.0.1:5000/recipe/add", json=data)
    return item


@bp.route("/edit/<id>", methods=["PUT"])
def edit_item_by_id(id):
    item = Item.query.get(id)
    data = request.get_json()
    name = data.get("name")
    # value = None
    # type = data.get("type")

    if name != None:
        item.name = name
    # if type != None:
    #     item.type = type
    db.session.commit()
    return jsonify(one_item_schema.dump(item))


@bp.route("/delete/<id>", methods=["DELETE"])
def delete_item_by_id(id):
    item = Item.query.get(id)
    if item != None:
        db.session.delete(item)
        db.session.commit()
        return jsonify("Item deleted successfully")
    return jsonify("Item not found")


@bp.route("/delete_name/<name>", methods=["DELETE"])
def delete_item_by_name(name):
    item = Item.query.filter_by(name=name).first()
    if item != None:
        db.session.delete(item)
        db.session.commit()
        return jsonify("Item deleted successfully")
    return jsonify("Item not found")


@bp.route("/skip", methods=['POST'])
@fp.auth_required
def skip_item_by_id():
    data = request.get_json()
    item_id = data.get("id")
    profile = fp.current_user().get_active_profile()
    # item = Item.query.get(id)

    skip = Skip(item_id=item_id,profile_id=profile.id, time=convert_to_time_format(datetime.now()))
    db.session.add(skip)
    db.session.commit()
    return jsonify(one_skip_schema.dump(skip))


@bp.route("/skips/get", methods=['GET'])
def get_all_skips():
    return jsonify(multi_skip_schema.dump(Skip.query.all()))

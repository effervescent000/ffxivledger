from flask import Blueprint, flash, json, redirect, render_template, request, url_for, jsonify, current_app
import flask_praetorian as fp

import requests as req

from .models import Item, Transaction, Stock
from .schema import ItemSchema, StockSchema, TransactionSchema
from . import db

bp = Blueprint("item", __name__, url_prefix="/item")
one_item_schema = ItemSchema()
multi_item_schema = ItemSchema(many=True)
multi_transaction_schema = TransactionSchema(many=True)
multi_stock_schema = StockSchema(many=True)


@bp.route("/get/<id>", methods=["GET"])
def get_item_by_value(id):
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
def get_stock_list():
    user_id = fp.current_user().id
    stock_list = Stock.query.filter(Stock.user_id == user_id, Stock.amount > 0).all()
    return jsonify(multi_stock_schema.dump(stock_list))


@bp.route("/get/all", methods=["GET"])
def get_all_items():
    return jsonify(multi_item_schema.dump(Item.query.all()))


# @bp.route("/add", methods=["POST"])
# @login_required
# @admin_required
# def create_item():
#     data = request.get_json()
#     name = data.get("name")
#     value = None
#     type = data.get("type")

#     if name != None:
#         value = name_to_value(name)
#     else:
#         return jsonify("Must return a name")
#     if type == None:
#         return jsonify("Must return a type")

#     new_item = Item(name=name, value=value, type=type)
#     db.session.add(new_item)
#     db.session.commit()
#     return jsonify(one_item_schema.dump(new_item))


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


# @bp.route('/edit/new', methods=('GET', 'POST'))
# @login_required
# @admin_required
# def create_item():
#     form = CreateItemForm()
#     if request.method == 'POST':
#         # TODO make this prevent duplicate item entry
#         new_item = Item(
#             name=form.item_name.data,
#             value=name_to_value(form.item_name.data),
#             type=form.item_type.data
#         )
#         db.session.add(new_item)
#         db.session.commit()
#         return redirect(url_for('item.manage_items'))
#     return render_template('ffxivledger/item_edit.html', form=form)


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

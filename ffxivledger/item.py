from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, current_user
import requests as req
import os

from ffxivledger.utils import admin_required, convert_to_time_format

from .models import Item, Transaction, Stock, Skip, Recipe, Component, User
from .schema import ItemSchema, StockSchema, TransactionSchema, SkipSchema, RecipeSchema
from . import db

bp = Blueprint("item", __name__, url_prefix="/item")
one_item_schema = ItemSchema()
multi_item_schema = ItemSchema(many=True)
multi_transaction_schema = TransactionSchema(many=True)
multi_stock_schema = StockSchema(many=True)
one_skip_schema = SkipSchema()
multi_skip_schema = SkipSchema(many=True)
one_recipe_schema = RecipeSchema()
multi_recipe_schema = RecipeSchema(many=True)

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
@jwt_required()
def get_stock_list():
    profile = current_user.get_active_profile()
    stock_list = Stock.query.filter(Stock.profile_id == profile.id, Stock.amount > 0).all()
    if stock_list != None:
        return jsonify(multi_stock_schema.dump(stock_list))
    else:
        return jsonify([])


@bp.route("/get/all", methods=["GET"])
def get_all_items():
    return jsonify(multi_item_schema.dump(Item.query.all()))


@bp.route("/add", methods=["POST"])
@jwt_required()
@admin_required
def create_item():
    return jsonify(one_item_schema.dump(process_item(request.get_json())))


# @bp.route("/add/search", methods=["POST"])
# @jwt_required()
# @admin_required
# def create_multiple_items_from_search():
#     data = request.get_json()
#     items_list = []
#     name = data.get("name")
#     search = req.get(f"https://xivapi.com/search?indexes=Item&string={name}&private_key={os.environ['XIVAPI_KEY']}").json()
#     results = search.get("Results")
#     for result in results:
#         result_name = result.get("Name")
#         if result_name.startswith(name):
#             items_list.append(process_item({"name": result_name}))
#     return jsonify(multi_item_schema.dump(items_list))


def get_item_id_from_search(results, search_term=None):
    if len(results) > 1:
        for result in results:
            if search_term != None:
                if search_term.lower() == result.get("Name").lower():
                    return result.get("ID")
            else:
                return results[0].get("ID")        
    elif len(results) == 1:
        return results[0].get("ID")
    else:
        # if no match is found, then return error
        return jsonify("No results found in XIVAPI search")


def process_item(data):
    # determine what type of data we're getting, a straight string or XIVAPI search results from front-end
    item_id = data.get("ID")
    # results = data.get("Results")
    if item_id == None:
        name = data.get("name")
        # GET request to xivapi to search for the item
        data = req.get(f"https://xivapi.com/search?indexes=Item&string={name}&private_key={os.environ['XIVAPI_KEY']}").json()
        # iterate through results (ideally only 1 result) for an exact name much (with .lower() run)
        item_id = get_item_id_from_search(data.get("Results"))

    item = Item.query.get(item_id)
    if item == None:
        # GET request to xivapi again for the item id
        # print(f"https://xivapi.com/Item/{item_id}&private_key={os.environ['XIVAPI_KEY']}")
        item_data = req.get(f"https://xivapi.com/Item/{item_id}?private_key={os.environ['XIVAPI_KEY']}").json()
        # print(item_data)
        # populate item's data from the return JSON
        item = Item(name=item_data.get("Name"), id=item_id)
        db.session.add(item)
        db.session.commit()
        # if any recipes are found, then query them as well and repeat the process
        recipes = item_data.get("Recipes")
        if recipes != None and len(recipes) > 0:
            for recipe in recipes:
                data = {"id": recipe.get("ID")}
                # req.post(f"{os.environ['BASE_URL']}/recipe/add", json=data)
                process_recipe(data)
    return item


def process_recipe(data):
    # data = request.get_json()
    # print(data)
    recipe_id = data["id"]
    # query xivapi for recipe id
    query = req.get(f"https://xivapi.com/Recipe/{recipe_id}?private_key={os.environ['XIVAPI_KEY']}").json()
    # make sure a result was returned
    if query.get("ID") == None:
        print(f"No recipe found with that ID ({recipe_id})")
        return jsonify("No recipe found with that ID")
    # create the recipe
    recipe = Recipe(
        id=query.get("ID"),
        job=query.get("ClassJob").get("Abbreviation"),
        level=query.get("RecipeLevelTable").get("ClassJobLevel"),
        item_id=query.get("ItemResult").get("ID"),
        item_quantity=query.get("AmountResult"),
    )
    db.session.add(recipe)
    db.session.commit()
    # iterate through each ItemIngredient, see if it exists in the db already. if not, pass it back to item/add to create a new one
    for i in range(10):
        # print(query.get(f"AmountIngredient{i}"))
        if query.get(f"AmountIngredient{i}") != 0:
            # print(f"I am adding component number {i}")
            # see if the item exists in the database, if not add it
            comp_id = query.get(f"ItemIngredient{i}").get("ID")
            if Item.query.get(comp_id) == None:
                post_data = {"ID": comp_id}
                # req.post(f"{os.environ['BASE_URL']}/item/add", json=post_data)
                process_item(post_data)
            # now generate the component
            # print(f"Attempting to add a component to recipe {recipe_id}")
            comp = Component(item_id=comp_id, item_quantity=query.get(f"AmountIngredient{i}"), recipe_id=recipe_id)
            # print(comp)
            db.session.add(comp)
            db.session.commit()
    return jsonify(one_recipe_schema.dump(recipe))


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


@bp.route("/skip", methods=["POST"])
@jwt_required()
def skip_item_by_id():
    data = request.get_json()
    item_id = data.get("id")
    profile = current_user.get_active_profile()
    # item = Item.query.get(id)

    skip = Skip(item_id=item_id, profile_id=profile.id, time=convert_to_time_format(datetime.now()))
    db.session.add(skip)
    db.session.commit()
    return jsonify(one_skip_schema.dump(skip))


@bp.route("/skips/get", methods=["GET"])
def get_all_skips():
    return jsonify(multi_skip_schema.dump(Skip.query.all()))

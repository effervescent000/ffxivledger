from flask import Blueprint, request, jsonify
import requests as req
import os

from . import db
from .models import Recipe, Component, Item

from .schema import RecipeSchema

bp = Blueprint("recipe", __name__, url_prefix="/recipe")

one_recipe_schema = RecipeSchema()
multi_recipe_schema = RecipeSchema(many=True)


@bp.route("/add", methods=["POST"])
def add_recipe_from_api():
    data = request.get_json()
    # print(data)
    recipe_id = data.get("id")
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
                post_data = {"name": query.get(f"ItemIngredient{i}").get("Name")}
                req.post(f"{os.environ['BASE_URL']}/item/add", json=post_data)
            # now generate the component
            print(f"Attempting to add a component to recipe {recipe_id}")
            comp = Component(item_id=comp_id, item_quantity=query.get(f"AmountIngredient{i}"), recipe_id=recipe_id)
            print(comp)
            db.session.add(comp)
            db.session.commit()
    return jsonify(one_recipe_schema.dump(recipe))


@bp.route("/get/<id>", methods=["GET"])
def get_recipe_by_id(id):
    return jsonify(one_recipe_schema.dump(Recipe.query.get(id)))


@bp.route("/get/all", methods=["GET"])
def get_all_recipes():
    return jsonify(multi_recipe_schema.dump(Recipe.query.all()))

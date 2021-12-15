import json
from os import abort
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, jsonify
)

from flask_login import login_required
import requests as req

from . import db
from .models import Recipe, Component, Item
from .forms import CreateRecipeForm
from .utils import get_item, admin_required, name_to_value
from .schema import RecipeSchema

bp = Blueprint('recipe', __name__, url_prefix='/recipe')

one_recipe_schema = RecipeSchema()
multi_recipe_schema = RecipeSchema(many=True)


@bp.route("/add", methods=['POST'])
def add_recipe_from_api():
    data = request.get_json()
    print(data)
    recipe_id = data.get("id")
    # query xivapi for recipe id
    query = req.get(f"https://xivapi.com/Recipe/{recipe_id}").json()
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
        item_quantity=query.get("AmountResult")
    )
    db.session.add(recipe)
    db.session.commit()
    # iterate through each ItemIngredient, see if it exists in the db already. if not, pass it back to item/add to create a new one
    for i in range(9):
        # print(query.get(f"AmountIngredient{i}"))
        if query.get(f"AmountIngredient{i}") != 0:
            # print(f"I am adding component number {i}")
            # see if the item exists in the database, if not add it
            comp_id = query.get(f"ItemIngredient{i}").get("ID")
            if Item.query.get(comp_id) == None:
                post_data = {"name": query.get(f"ItemIngredient{i}").get("Name")}
                req.post("http://127.0.0.1:5000/item/add", json=post_data)
            # now generate the component
            comp = Component(item_id=comp_id, item_quantity=query.get(f"AmountIngredient{i}"))
            db.session.add(comp)
            db.session.commit()
    return jsonify(one_recipe_schema.dump(recipe))


# @bp.route('/edit/<id>', methods=('GET', 'POST'))
# @login_required
# @admin_required
# def edit_recipe(id):
#     # first generate/prepopulate the form
#     recipe = Recipe.query.get(id)
#     form = CreateRecipeForm(product_name=recipe.product.item_value,
#                             product_quantity=recipe.product.item_quantity, 
#                             job_field=recipe.job)
    
#     for i in range(len(recipe.components) - 1):
#         form.line_item_list[i].item_value.data = recipe.components[i].item_value
#         form.line_item_list[i].item_quantity.data = recipe.components[i].item_quantity

#     # now we process the form
#     if request.method == 'POST':
#         product = Product.query.filter_by(recipe_id=id).one()
#         # components = Component.query.filter_by(recipe_id=id).all()
#         if product.item_value != form.product_name.data:
#             product.item_value = form.product_name.data
#         if product.item_quantity != form.product_quantity.data:
#             product.item_quantity = form.product_quantity.data
#         # for now component editing only works with changing quantities. If you screw up and put the wrong item as a component, delete the recipe and try again
#         for x in form.line_item_list.entries:
#             if x.item_value.data != '':
#                 component = Component.query.filter_by(recipe_id=id,item_value=x.item_value.data).one_or_none()
#                 if component is None:
#                     component = Component(item_value=x.item_value.data,item_quantity=x.item_quantity.data,recipe_id=id)
#                     db.session.add(component)
#                     db.session.commit()
#                 elif component.item_quantity != x.item_quantity.data:
#                     component.item_quantity = x.item_quantity.data
#                     db.session.commit()
#         db.session.commit()

#     return render_template('ffxivledger/recipe_edit.html', form=form)


# @bp.route('/view/<value>', methods=('GET', 'POST'))
# def view_recipes(value):
#     recipes = {}
#     product = get_item(value)
#     for x in Product.query.filter(Product.item_value == value).all():
#         component_list = [y for y in Component.query.filter(Component.recipe_id == x.recipe.id)]
#         recipes[x.recipe.id] = component_list
#     return render_template('ffxivledger/recipe_view.html', recipes=recipes, item=product)


# @bp.route('/manage')
# @login_required
# @admin_required
# def manage_recipes():
#     product_list = Product.query.all()
#     return render_template('ffxivledger/recipe_management.html', product_list=product_list)

@bp.route("/get/<id>", methods=['GET'])
def get_recipe_by_id(id):
    return jsonify(one_recipe_schema.dump(Recipe.query.get(id)))

@bp.route("/get/all", methods=['GET'])
def get_all_recipes():
    return jsonify(multi_recipe_schema.dump(Recipe.query.all()))
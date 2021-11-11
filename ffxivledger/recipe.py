from os import abort
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask.wrappers import Response
from flask_login import login_required
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList

from . import db
from .models import Item, Recipe, Component, Product
from .forms import CreateRecipeForm, RecipeLineForm
from .utils import get_item, admin_required

bp = Blueprint('recipe', __name__, url_prefix='/recipe')


@bp.route('/edit/new', methods=('GET', 'POST'))
@login_required
@admin_required
def create_recipe():
    form = CreateRecipeForm()
    if request.method == 'POST':
        selected_product = get_item(form.product_name.data)
        components = {}
        for x in form.line_item_list.entries:
            if x.item_value.data != '':
                components[x.item_value.data] = x.item_quantity.data
        if len(components) > 0:
            recipe_new = Recipe(job=form.job_field.data)
            db.session.add(recipe_new)
            db.session.commit()
            # retrieve this recipe again
            product_new = Product(item_value=selected_product.value, item_quantity=form.product_quantity.data,
                                  recipe_id=recipe_new.id)
            db.session.add(product_new)
            db.session.commit()
            # now create components
            for k, v in components.items():
                if k is not None and v is not None:
                    component_new = Component(item_value=k, item_quantity=v, recipe_id=recipe_new.id)
                    db.session.add(component_new)
                    db.session.commit()
    # TODO make the product selectField pre-select the product passed as an argument if there is one
    # if value is not None:
    #     form.product_name.default=value
    #     form.process()
    return render_template('ffxivledger/recipe_edit.html', form=form)


@bp.route('/edit/<id>', methods=('GET', 'POST'))
@login_required
@admin_required
def edit_recipe(id):
    # first generate/prepopulate the form
    recipe = Recipe.query.get(id)
    form = CreateRecipeForm(product_name=recipe.product.item_value,
                            product_quantity=recipe.product.item_quantity, 
                            job_field=recipe.job)
    
    for i in range(len(recipe.components) - 1):
        form.line_item_list[i].item_value.data = recipe.components[i].item_value
        form.line_item_list[i].item_quantity.data = recipe.components[i].item_quantity

    # now we process the form
    if request.method == 'POST':
        product = Product.query.filter_by(recipe_id=id).one()
        # components = Component.query.filter_by(recipe_id=id).all()
        if product.item_value != form.product_name.data:
            product.item_value = form.product_name.data
        if product.item_quantity != form.product_quantity.data:
            product.item_quantity = form.product_quantity.data
        # for now component editing only works with changing quantities. If you screw up and put the wrong item as a component, delete the recipe and try again
        for x in form.line_item_list.entries:
            if x.item_value.data != '':
                component = Component.query.filter_by(recipe_id=id,item_value=x.item_value.data).one_or_none()
                if component is None:
                    component = Component(item_value=x.item_value.data,item_quantity=x.item_quantity.data,recipe_id=id)
                    db.session.add(component)
                    db.session.commit()
                elif component.item_quantity != x.item_quantity.data:
                    component.item_quantity = x.item_quantity.data
                    db.session.commit()
        db.session.commit()

    return render_template('ffxivledger/recipe_edit.html', form=form)


@bp.route('/view/<value>', methods=('GET', 'POST'))
def view_recipes(value):
    recipes = {}
    product = get_item(value)
    for x in Product.query.filter(Product.item_value == value).all():
        component_list = [y for y in Component.query.filter(Component.recipe_id == x.recipe.id)]
        recipes[x.recipe.id] = component_list
    return render_template('ffxivledger/recipe_view.html', recipes=recipes, item=product)


@bp.route('/manage')
@login_required
@admin_required
def manage_recipes():
    product_list = Product.query.all()
    return render_template('ffxivledger/recipe_management.html', product_list=product_list)

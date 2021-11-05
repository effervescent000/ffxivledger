from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from . import db
from .models import Item, Recipe, Component, Product
from .forms import CreateRecipeForm
from .utils import get_item

bp = Blueprint('recipe', __name__, url_prefix='/recipe')


@bp.route('/edit/new', methods=('GET', 'POST'))
def create_recipe(product=None):
    form = CreateRecipeForm()
    if request.method == 'POST':
        # this code will probably not work as is, this is just a skeleton/idea of what i expect it to look like.
        # for now I want to save all variables and then check that all are valid, and then at the end actually create
        # the recipe and components and stuff
        selected_product = get_item(form.product_name.data)
        components = {}
        for x in form.line_item_list.entries:
            # TODO figure out how to deal with this "none/blank" situation
            if x.item_value.data is not None:
                components[x.item_value.data] = x.item_quantity.data
        if len(components) > 0:
            recipe_new = Recipe(job=form.job_field.data)
            db.session.add(recipe_new)
            db.session.commit()
            # retrieve this recipe again
            # I'm not sure if this will work
            product_new = Product(item_value=selected_product.value, item_quantity=form.product_quantity.data,
                                  recipe_id=recipe_new.id)
            db.session.add(product_new)
            db.session.commit()
            # now create components
            for k, v in components.items():
                component_new = Component(item_value=k, item_quantity=v, recipe_id=recipe_new.id)
                db.session.add(component_new)
                db.session.commit()
    # TODO make the product selectField pre-select the product passed as an argument if there is one
    if product is not None:
        form.product_name.default=product
        form.process()
    return render_template('ffxivledger/recipe_edit.html', form=form)


@bp.route('/view/<value>', methods=('GET', 'POST'))
def view_recipes(value):
    recipes = []
    # TODO i think i can do this with a list comprehension
    for x in Product.query.filter(Product.item_value == value).all():
        recipes.append(x.recipe)
    return render_template('ffxivledger/recipe_view.html', recipes=recipes)

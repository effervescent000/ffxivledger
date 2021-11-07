from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from . import db
from .models import Item, Recipe, Component, Product
from .forms import CreateRecipeForm
from .utils import get_item

bp = Blueprint('recipe', __name__, url_prefix='/recipe')


@bp.route('/edit/new', methods=('GET', 'POST'))
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
            # I'm not sure if this will work
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


@bp.route('/view/<value>', methods=('GET', 'POST'))
def view_recipes(value):
    recipes = {}
    product = get_item(value)
    # TODO i think i can do this with a list comprehension
    for x in Product.query.filter(Product.item_value == value).all():
        component_list = [y for y in Component.query.filter(Component.recipe_id == x.recipe.id)]
        recipes[x.recipe.id] = component_list
    return render_template('ffxivledger/recipe_view.html', recipes=recipes, item=product)

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from . import db
from .models import Item, Recipe, Component, Product
from .forms import CreateRecipeForm

bp = Blueprint('recipe', __name__, url_prefix='/recipe')


@bp.route('/edit/new', methods=('GET', 'POST'))
def create_recipe():
    if request.method == 'POST':
        pass
    # not passing any argument on how many form inputs to create, just create six since this is to make a recipe
    form = CreateRecipeForm()
    return render_template('ffxivledger/recipe_edit.html', form=form)

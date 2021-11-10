from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import login_required

from .models import Item, Price
from . import db
from .utils import get_item, name_to_value, admin_required
from .forms import CreateItemForm

bp = Blueprint('item', __name__, url_prefix='/item')


@bp.route('/view/<value>', methods=('GET', 'POST'))
def view_item(value):
    item = get_item(value)

    sale_price_list = Price.query.filter(Price.item_value == value, Price.price_input > 0).all()
    purchase_price_list = Price.query.filter(Price.item_value == value, Price.price_input < 0).all()
    return render_template('ffxivledger/item_view.html', item=item, sale_price_list=sale_price_list,
                           purchase_price_list=purchase_price_list)


@bp.route('/edit/new', methods=('GET', 'POST'))
@login_required
@admin_required
def create_item():
    form = CreateItemForm()
    if request.method == 'POST':
        name = form.item_name.data
        value = name_to_value(name)
        item_type = form.item_type.data

        new_item = Item(name=name, value=value, type=item_type)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('dashboard.index'))
    return render_template('ffxivledger/item_edit.html', form=form)

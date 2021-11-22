from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import login_required

from .models import Item, Transaction
from . import db
from .utils import get_item, name_to_value, admin_required, rename_item
from .forms import CreateItemForm

bp = Blueprint('item', __name__, url_prefix='/item')


@bp.route('/view/<value>', methods=('GET', 'POST'))
def view_item(value):
    item = get_item(value)

    sale_list = Transaction.query.filter(Transaction.item_value == value, Transaction.gil_value > 0).all()
    purchase_list = Transaction.query.filter(Transaction.item_value == value, Transaction.gil_value < 0).all()
    return render_template('ffxivledger/item_view.html', item=item, sale_price_list=sale_list,
                           purchase_price_list=purchase_list)


@bp.route('/edit/new', methods=('GET', 'POST'))
@login_required
@admin_required
def create_item():
    form = CreateItemForm()
    if request.method == 'POST':
        name = form.item_name.data
        value = name_to_value(name)
        # TODO make this prevent duplicate item entry
        item_type = form.item_type.data

        new_item = Item(name=name, value=value, type=item_type)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('item.manage_items'))
    return render_template('ffxivledger/item_edit.html', form=form)


@bp.route('/edit/<value>', methods=('GET', 'POST'))
@login_required
@admin_required
def edit_item(value):
    item = get_item(value)
    form = CreateItemForm(item_name=item.name,item_type=item.type)
    if form.validate_on_submit():
        if item.name != form.item_name.data:
            rename_item(item, form.item_name.data)
        if item.type != form.item_type.data:
            item.type = form.item_type.data
        db.session.commit()
        return redirect(url_for('item.manage_items'))
    return render_template('ffxivledger/item_edit.html', form=form)


@bp.route('/manage')
@login_required
@admin_required
def manage_items():
    item_list = Item.query.all()
    return render_template('ffxivledger/item_management.html', item_list=item_list)

@bp.route('/delete/<value>', methods=('GET', 'POST'))
@login_required
@admin_required
def delete_item(value):
    item = Item.query.get(value)
    if item is not None:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('item.manage_items'))
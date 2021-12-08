from flask import (
    Blueprint, flash, json, redirect, render_template, request, url_for, jsonify
)
from flask_login import login_required

from .models import Item, Transaction
from .schema import ItemSchema, TransactionSchema
from . import db
from .utils import get_item, name_to_value, admin_required, rename_item
from .forms import CreateItemForm

bp = Blueprint('item', __name__, url_prefix='/item')
one_item_schema = ItemSchema()
multi_item_schema = ItemSchema(many=True)
multi_transaction_schema = TransactionSchema(many=True)


@bp.route('/view/<value>', methods=['GET'])
def get_item_by_value(value):
    item = Item.query.get(value)
    return jsonify(one_item_schema.dump(item))
# def view_item(value):
#     return render_template(
#         'ffxivledger/item_view.html', 
#         item=get_item(value), 
#         sale_price_list=Transaction.query.filter(Transaction.item_value == value, Transaction.gil_value > 0).all(),
#         purchase_price_list=Transaction.query.filter(Transaction.item_value == value, Transaction.gil_value < 0).all()
#     )


@bp.route('/view/<value>/sales', methods=['GET'])
def get_item_sales(value):
    sales_list = Transaction.query.filter(Transaction.item_value==value, Transaction.gil_value>0).all()
    return jsonify(multi_transaction_schema.dump(sales_list))


@bp.route('/view/<value>/purchases', methods=['GET'])
def get_item_purchases(value):
    purchases_list = Transaction.query.filter(Transaction.item_value==value, Transaction.gil_value<0).all()
    return jsonify(multi_transaction_schema.dump(purchases_list))

@bp.route('/edit/new', methods=['POST'])
@login_required
@admin_required
def create_item():
    data = request.get_json()
    name = data.get('name')
    value = None
    type = data.get('type')

    if name != None:
        value = name_to_value(name)
    else:
        return jsonify('Must return a name')
    if type == None:
        return jsonify('Must return a type')
    
    new_item = Item(name=name, value=value, type=type)
    db.session.add(new_item)
    db.session.commit()
    return jsonify(one_item_schema.dump(new_item))
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


@bp.route('edit/<value>', methods=['PUT'])
def edit_item(value):
    item = get_item(value)
    data = request.get_json()
    name = data.get('name')
    # value = None
    type = data.get('type')

    if name != None:
        item.value = name_to_value(name)
        item.name = name
    if type != None:
        item.type = type
    db.session.commit()
    return jsonify(one_item_schema.dump(item))
    

# @bp.route('/edit/<value>', methods=('GET', 'POST'))
# @login_required
# @admin_required
# def edit_item(value):
#     item = get_item(value)
#     form = CreateItemForm(item_name=item.name,item_type=item.type)
#     if form.validate_on_submit():
#         if item.name != form.item_name.data:
#             rename_item(item, form.item_name.data)
#         if item.type != form.item_type.data:
#             item.type = form.item_type.data
#         db.session.commit()
#         return redirect(url_for('item.manage_items'))
#     return render_template('ffxivledger/item_edit.html', form=form)


@bp.route('/manage')
@login_required
@admin_required
def manage_items():
    return render_template('ffxivledger/item_management.html', item_list=Item.query.all())

@bp.route('/delete/<value>', methods=('GET', 'POST'))
@login_required
@admin_required
def delete_item(value):
    item = Item.query.get(value)
    if item is not None:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('item.manage_items'))
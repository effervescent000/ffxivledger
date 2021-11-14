from datetime import timedelta
from math import floor
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, current_app
)
from flask_login import current_user

from .models import Item, Stock, Transaction, Recipe, Component, Product
from .utils import get_item, convert_string_to_datetime
from .forms import CraftingQueueForm, CraftingOutputForm

bp = Blueprint('crafting', __name__, url_prefix='/craft')

@bp.route('/queue', methods=('GET', 'POST'))
def view_queue():
    queue_form = CraftingQueueForm()
    log_form = CraftingOutputForm()
    if request.method == 'POST':
        if queue_form.queue_button.data:
            queue_amount = queue_form.queue_dropdown.data
            queue_form.queue_text.data = queue_to_string(generate_queue(queue_amount))
            return render_template('ffxivledger/crafting.html', queue_form=queue_form, log_form=log_form, queue_amount=queue_amount)
        elif log_form.clear_button.data:
            pass
        else:
            print('Neither button was pressed???')
    return render_template('ffxivledger/crafting.html', queue_form=queue_form, log_form=log_form)

def queue_to_string(craft_list):
    text = ''
    for x in craft_list:
        new_string = '{} for {} {}\n'.format(craft_list[0], craft_list[1], craft_list[2])
        text = text + new_string
        return text

def generate_queue(num):
    num = int(num)
    primary_craft_list = []
    secondary_craft_list = []
    tertiary_craft_list = []

    for x in Product.query.all():
        stock = get_item(x.item_value).stock
        if len(stock) > 1:
            print('Stock data is screwed up for {}'.format(x.item_value))
        else:
            if stock.amount == 0:
                transaction_list = Transaction.query.filter_by(item_value=x.item_value, user_id=current_user.id).all()
                sales_list = [y for y in transaction_list if (y.gil_value > 0 and y.amount < 0)]
                if len(sales_list) > 0:
                    gph = get_gph(x.item_value, sales_list)
                    if gph is not None:
                        primary_craft_list.append((x.item_value, gph, 'gph'))
                    else:
                        secondary_craft_list.append((x.item_value, get_profit(x.item_value), 'gil'))
                else:
                    tertiary_craft_list.append((x.item_value, get_profit(x.item_value), 'gil'))
    primary_craft_list.sort(key=get_gph, reverse=True)
    secondary_craft_list.sort(key=get_profit, reverse=True)
    tertiary_craft_list.sort(key=get_profit, reverse=True)

    craft_list = []
    if len(primary_craft_list) < num:
        craft_list = [x for x in primary_craft_list]
    else:
        for i in range(num):
            craft_list.append(primary_craft_list[i])
    if len(craft_list) < num:
        craft_list = get_from_craft_lists(craft_list, secondary_craft_list, num)
        if len(craft_list) < num:
            craft_list = get_from_craft_lists(craft_list, tertiary_craft_list, num)
    return craft_list


def get_from_craft_lists(craft_list, secondary_craft_list, num):
    n = num - len(craft_list)
    if n < len(secondary_craft_list):
        for i in range(n):
            craft_list.append(secondary_craft_list)
    else:
        for i in range(len(secondary_craft_list)):
            craft_list.append(secondary_craft_list[i])
    return craft_list

def get_gph(item_value, sales_list=None):
    transaction_list = Transaction.query.filter_by(item_value=item_value, user_id=current_user.id).all()
    if sales_list is None:
        sales_list = [x for x in transaction_list if (x.gil_value > 0 and x.amount < 0)]
    restock_list = [x for x in transaction_list if (x.gil_value == 0 and x.amount > 0)]

    if len(sales_list) > 0 and len(restock_list) > 0:
        deltas = []
        for x in sales_list:
            matching_restock = match_stock(x.time, restock_list)
            if matching_restock is not None:
                deltas.append(convert_string_to_datetime(x.time), convert_string_to_datetime(x.time))
                restock_list.remove(matching_restock)
        if len(deltas) > 0:
            total_time = timedelta()
            for x in deltas:
                total_time += x
            avg_time = total_time / len(deltas)
            return floor(get_profit(item_value) / (avg_time.days * 24 + avg_time.seconds / 3600))
    return None


def match_stock(sale_time, restock_list):
    sale_time = convert_string_to_datetime(sale_time)
    for x in restock_list:
        if convert_string_to_datetime(x.time) < sale_time:
            # time_gap = sale_time - x
            # TODO option here to disregard matches with a time gap longer than n
            return x
    return None


def get_profit(item_value):
    return get_average_price(item_value, mode='s') - get_crafting_cost(item_value)

def get_average_price(item_value,mode=None):
    price_list = []
    transaction_list = Transaction.query.filter_by(item_value=item_value, user_id=current_user.id).all()
    if mode is None:
        price_list = [x.gil_value for x in transaction_list if x.gil_value != 0]
    elif mode == 'sale' or mode == 'sales' or mode == 1 or mode == 's':
        price_list = [x.gil_value for x in transaction_list if x.gil_value > 0]
    elif mode == 'purchase' or mode == 'purchases' or mode == -1 or mode == 'p':
        price_list = [x.gil_value for x in transaction_list if x.gil_value < 0]
    else:
        print('Invalid mode passed to get_average_price')
    if len(price_list) > 0:
        return sum(price_list) / len(price_list)
    else:
        return None


def get_crafting_cost(item_value):
    item = get_item(item_value)
    if item.type != 'material':
        products = Product.query.filter_by(item_value=item_value).all()
        if len(products) > 0:
            # right now this will double-count the cost of products with more than 1 recipe
            craft_cost = 0
            recipe_list = [x.recipe_id for x in products]
            for x in recipe_list:
                recipe = Recipe.query.get(x)
                for x in recipe.components:
                    craft_cost += get_crafting_cost(item_value)
            return craft_cost
    else:
        craft_cost = get_average_price(item_value, mode='p')
        return craft_cost
    return None
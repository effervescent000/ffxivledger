from datetime import timedelta
from math import floor
from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app, jsonify
from flask_login import current_user

from .models import Item, Stock, Transaction, Recipe, Component, Product
from .utils import get_item, convert_string_to_datetime, get_user_id

bp = Blueprint("crafting", __name__, url_prefix="/craft")


@bp.route("/get_queue/<amount>", methods=["GET"])
def get_queue(amount):
    user_id = current_user.id
    queue = Queue(amount, user_id)
    return jsonify(queue.generate_queue())


def list_to_string(list_arg):
    text = ""
    if len(list_arg) > 0:
        if isinstance(list_arg[0], tuple):
            for x in list_arg:
                new_string = "{} for {} {}\n".format(x[0], x[1], x[2])
                text += new_string
        else:
            for x in list_arg:
                new_string = "{}\n".format(x)
                text += new_string
    return text


class Queue:
    def __init__(self, num, user_id):
        self.num = int(num)
        self.user_id = user_id

    def generate_queue(self):
        primary_craft_list = []
        secondary_craft_list = []
        tertiary_craft_list = []
        error_list = []

        for product in Product.query.all():
            stock = Stock.query.filter_by(item_value=product.item_value, user_id=self.user_id).all()
            if len(stock) > 1:
                print("Stock data is screwed up for {}".format(product.item_value))
            else:
                if len(stock) == 0 or stock[0].amount == 0:
                    transaction_list = Transaction.query.filter_by(
                        item_value=product.item_value, user_id=self.user_id
                    ).all()
                    sales_list = [
                        transaction
                        for transaction in transaction_list
                        if (transaction.gil_value > 0 and transaction.amount < 0)
                    ]
                    if len(sales_list) > 0:
                        result = self.get_gph(product.item_value, sales_list, error_list)
                        gph = result[0]
                        error_list = result[1]
                        if gph is not None:
                            primary_craft_list.append((product.item_value, gph, "gph"))
                        else:
                            result = self.get_profit(product.item_value, error_list)
                            profit = result[0]
                            error_list = result[1]
                            secondary_craft_list.append((product.item_value, profit, "gil"))
                    else:
                        result = self.get_profit(product.item_value, error_list)
                        profit = result[0]
                        error_list = result[1]
                        tertiary_craft_list.append((product.item_value, profit, "gil"))
        primary_craft_list.sort(key=self.get_gph, reverse=True)
        secondary_craft_list.sort(key=self.get_profit, reverse=True)
        tertiary_craft_list.sort(key=self.get_profit, reverse=True)

        craft_list = []
        if len(primary_craft_list) < self.num:
            craft_list = [craft for craft in primary_craft_list]
        else:
            for i in range(self.num):
                craft_list.append(primary_craft_list[i])
        if len(craft_list) < self.num:
            craft_list = self.get_from_craft_lists(craft_list, secondary_craft_list, self.num)
            if len(craft_list) < self.num:
                craft_list = self.get_from_craft_lists(craft_list, tertiary_craft_list, self.num)
        return craft_list, error_list

    def get_from_craft_lists(self, craft_list, secondary_craft_list, num):
        n = num - len(craft_list)
        if n < len(secondary_craft_list):
            for i in range(n):
                craft_list.append(secondary_craft_list[i])
        else:
            for i in range(len(secondary_craft_list)):
                craft_list.append(secondary_craft_list[i])
        return craft_list

    def get_gph(self, item_value, sales_list=None, error_list=None):
        new_error_list = []
        transaction_list = Transaction.query.filter_by(item_value=item_value, user_id=get_user_id()).all()
        if sales_list is None:
            sales_list = [x for x in transaction_list if (x.gil_value > 0 and x.amount < 0)]
        restock_list = [x for x in transaction_list if (x.gil_value == 0 and x.amount > 0)]

        if len(sales_list) > 0 and len(restock_list) > 0:
            deltas = []
            for x in sales_list:
                matching_restock = self.match_stock(x.time, restock_list)
                if matching_restock is not None:
                    deltas.append(convert_string_to_datetime(x.time), convert_string_to_datetime(x.time))
                    restock_list.remove(matching_restock)
            if len(deltas) > 0:
                total_time = timedelta()
                for x in deltas:
                    total_time += x
                avg_time = total_time / len(deltas)
                if error_list is None:
                    return floor(self.get_profit(item_value) / (avg_time.days * 24 + avg_time.seconds / 3600))
                else:
                    profit = self.get_profit(item_value)
                    new_error_list = profit[1]
                    profit = profit[0]
                    return [
                        floor(profit / (avg_time.days * 24 + avg_time.seconds / 3600)),
                        error_list + new_error_list,
                    ]
        return None

    def match_stock(self, sale_time, restock_list):
        sale_time = convert_string_to_datetime(sale_time)
        for x in restock_list:
            if convert_string_to_datetime(x.time) < sale_time:
                # time_gap = sale_time - x
                # TODO option here to disregard matches with a time gap longer than n
                return x
        return None

    def get_profit(self, item_value, error_list=None):
        new_error_list = []
        new_item_value = None
        if isinstance(item_value, tuple):
            new_item_value = item_value[0]
        else:
            new_item_value = item_value
        avg = self.get_average_price(new_item_value, mode="s")
        result = self.get_crafting_cost(new_item_value, new_error_list)
        cost = result[0]
        if avg is None:
            avg = 0
        if cost is None:
            print("{} has a crafting cost of None, setting to 0".format(new_item_value))
            cost = 0
        if error_list is not None:
            new_error_list = result[1]
            return [avg - cost, error_list + new_error_list]
        else:
            return avg - cost

    def get_average_price(self, item_value, mode=None):
        price_list = []
        transaction_list = Transaction.query.filter_by(item_value=item_value, user_id=self.user_id).all()
        if len(transaction_list) > 0:
            if mode is None:
                price_list = [x.gil_value for x in transaction_list if x.gil_value != 0]
            elif mode == "sale" or mode == "sales" or mode == 1 or mode == "s":
                price_list = [x.gil_value for x in transaction_list if x.gil_value > 0]
            elif mode == "purchase" or mode == "purchases" or mode == -1 or mode == "p":
                price_list = [x.gil_value * -1 for x in transaction_list if x.gil_value < 0]
            else:
                print("Invalid mode passed to get_average_price")

        if len(price_list) > 0:
            return sum(price_list) / len(price_list)
        else:
            return None

    def get_crafting_cost(self, item_value, error_list=None):
        item = get_item(item_value)
        if error_list is None:
            error_list = []
        if item.type != "material":
            products = Product.query.filter_by(item_value=item_value).all()
            if len(products) > 0:
                # right now this will double-count the cost of products with more than 1 recipe
                craft_cost = 0
                recipe_list = [x.recipe_id for x in products]
                for x in recipe_list:
                    recipe = Recipe.query.get(x)
                    for y in recipe.components:
                        result = self.get_crafting_cost(y.item_value, error_list)
                        if result is None:
                            error_list.append("Component {} returned None for crafting cost".format(y.item_value))
                        else:
                            y_cost = result[0]
                            error_list = result[1]
                            craft_cost += y_cost
                return [craft_cost, error_list]
        else:
            craft_cost = self.get_average_price(item_value, mode="p")
            if craft_cost is None:
                error_list.append("{} has None for craft_cost, setting to 0".format(item_value))
                craft_cost = 0
            return [craft_cost, error_list]
        return None

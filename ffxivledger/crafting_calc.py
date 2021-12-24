from datetime import timedelta, datetime
from math import floor
from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app, jsonify
from flask_login import current_user
import requests as req
from flask_cors import CORS

from . import db
from .models import Item, Stock, Transaction, Recipe, Component, User, Profile
from .utils import get_item, convert_string_to_datetime, convert_to_time_format, get_user_id

bp = Blueprint("crafting", __name__, url_prefix="/craft")
CORS(bp)

@bp.route("/get_queue/<amount>", methods=["GET"])
def get_queue(amount):
    user_id = current_user.id
    queue = Queue(amount)
    full_queue = queue.generate_queue()
    short_queue = []
    while len(short_queue) < int(amount):
        short_queue.append(full_queue.pop(0))
    return jsonify(short_queue)


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
    def __init__(self, num):
        self.num = num
        self.user_id = current_user.id
        self.profile = Profile.query.filter_by(user_id=self.user_id).first()
    
    # method to iterate over recipes in DB and find the highest gil/hour ones to craft
    def generate_queue(self):
        queue = []
        # for now just do all jobs but I would like to make it so you can pick one or a couple or w/e
        for recipe in Recipe.query.all():
            # exclude items that are in stock already
            stock = Stock.query.filter_by(item_id=recipe.item_id, user_id=self.user_id).first()
            if stock == None or stock.amount == 0:
                # only include top-level craftables (nothing that's a component of something else)
                # (this isn't perfect b/c it excludes certain pieces of gear but I'll figure that out later)
                if Component.query.filter_by(item_id=recipe.item_id).first() == None:
                    if recipe.job == "ALC":
                        if self.profile.alc_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
                    elif recipe.job == "ARM":
                        if self.profile.arm_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
                    elif recipe.job == "BSM":
                        if self.profile.bsm_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
                    elif recipe.job == "CRP":
                        if self.profile.crp_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
                    elif recipe.job == "CUL":
                        if self.profile.cul_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
                    elif recipe.job == "GSM":
                        if self.profile.gsm_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
                    elif recipe.job == "LTW":
                        if self.profile.ltw_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
                    elif recipe.job == "WVR":
                        if self.profile.wvr_level >= recipe.level:
                            queue.append((recipe.item.name, self.get_gph(Item.query.get(recipe.item_id))))
        queue.sort(reverse=True, key=lambda x : x[1])
        return queue

    # method to calculate crafting cost recursively
    def get_crafting_cost(self, item):
        # first, declare crafting cost variable
        crafting_cost = 0
        # next, check if the item can be crafted
        if len(item.recipes) > 0:
            # if yes, iterate through recipes (this will result in items with more than 1 recipe having doubled up crafting costs)
            for recipe in item.recipes:
                # iterate through the components of each recipe to get their individual crafting cost
                for component in recipe.components:
                    crafting_cost += self.get_crafting_cost(component.item) * component.item_quantity
                # this cuts off after the first recipe
                return crafting_cost / recipe.item_quantity
        else:
            # if no, query Universalis and get the going rate of the material, return this
            self.check_cached_data(item)
            return item.price

    # method to check freshness of queried data and requery if necessary
    def check_cached_data(self, item):
        # first check when stats_updated was last updated, if > 12hrs ago, requery
        # grab stats_updated and convert to a date if it's valid
        now = datetime.now()
        if item.stats_updated != None:
            last_update = convert_string_to_datetime(item.stats_updated)
            # print(f"I think it's been {(now - last_update).total_seconds() / 3600} hours since last update for item {item.name}")
            # if it's been more than 6 hours:
            if (now - last_update).total_seconds() / 3600 > 6:
                print(f"I think it's been more than 6 hrs, updating data for {item.name}")
                self.update_cached_data(item)
        else:
            print(f"No data for {item.name}, updating...")
            self.update_cached_data(item)

    # method to actually query universalis
    def update_cached_data(self, item):
        # first, get world data as normal
        profile_world = self.profile.world
        data = req.get(f"https://universalis.app/api/{profile_world}/{item.id}").json()
        # if world data is below a certain # of listings, then grab datacenter data
        if len(data.get("listings")) < 5:
            # retrieve name of DC
            search = req.get(f"https://xivapi.com/search?indexes=World&string={profile_world}").json()
            world_id = search.get("Results")[0].get("ID")
            world_search = req.get(f"https://xivapi.com/World/{world_id}").json()
            dc_name = world_search.get("DataCenter").get("Name")
            # overwrite data with dc data for given item
            data = req.get(f"https://universalis.app/api/{dc_name}/{item.id}").json()
            # now update item stats
            item.stats_updated = convert_to_time_format(datetime.now())
            item.price = data.get("averagePrice")
            item.sales_velocity = data.get("regularSaleVelocity")
            db.session.commit()
        else:
            # instead of using averagePrice, use minPrice (only with world data, continue using averagePrice for DC data)
            item.stats_updated = convert_to_time_format(datetime.now())
            item.price = data.get("minPrice")
            item.sales_velocity = data.get("regularSaleVelocity")
            db.session.commit()
        # include checks for vanity items (does it require lvl 1 to use?), if so then do not pay attention to NQ vs HQ
        # if it's an actual gear item, then preferentially use HQ data sources when available


    # method to estimate profit/hour
    def get_gph(self, item):
        # first, get crafting cost
        crafting_cost = self.get_crafting_cost(item)
        print(f"{item.name} costs {crafting_cost} gil to make")
        # next, retrieve sale value of finished product
        self.check_cached_data(item)
        profit = item.price - crafting_cost
        # return: multiply profit by sale velocity HQ (which I believe is calculated per day)
        return round((profit * item.sales_velocity) / 24)

# class Queue:
#     def __init__(self, num, user_id):
#         self.num = int(num)
#         self.user_id = user_id

#     def generate_queue(self):
#         primary_craft_list = []
#         secondary_craft_list = []
#         tertiary_craft_list = []
#         error_list = []
#         product_list = [x for x in Item.query.all() if x.recipes != None]

#         for product in product_list:
#             stock = Stock.query.filter_by(item_value=product.value, user_id=self.user_id).all()
#             if len(stock) > 1:
#                 print("Stock data is screwed up for {}".format(product.value))
#             else:
#                 if len(stock) == 0 or stock[0].amount == 0:
#                     transaction_list = Transaction.query.filter_by(
#                         item_value=product.value, user_id=self.user_id
#                     ).all()
#                     sales_list = [
#                         transaction
#                         for transaction in transaction_list
#                         if (transaction.gil_value > 0 and transaction.amount < 0)
#                     ]
#                     if len(sales_list) > 0:
#                         result = self.get_gph(product.value, sales_list, error_list)
#                         gph = result[0]
#                         error_list = result[1]
#                         if gph is not None:
#                             primary_craft_list.append((product.value, gph, "gph"))
#                         else:
#                             result = self.get_profit(product.value, error_list)
#                             profit = result[0]
#                             error_list = result[1]
#                             secondary_craft_list.append((product.value, profit, "gil"))
#                     else:
#                         result = self.get_profit(product.value, error_list)
#                         profit = result[0]
#                         error_list = result[1]
#                         tertiary_craft_list.append((product.value, profit, "gil"))
#         primary_craft_list.sort(key=self.get_gph, reverse=True)
#         secondary_craft_list.sort(key=self.get_profit, reverse=True)
#         tertiary_craft_list.sort(key=self.get_profit, reverse=True)

#         craft_list = []
#         if len(primary_craft_list) < self.num:
#             craft_list = [craft for craft in primary_craft_list]
#         else:
#             for i in range(self.num):
#                 craft_list.append(primary_craft_list[i])
#         if len(craft_list) < self.num:
#             craft_list = self.get_from_craft_lists(craft_list, secondary_craft_list, self.num)
#             if len(craft_list) < self.num:
#                 craft_list = self.get_from_craft_lists(craft_list, tertiary_craft_list, self.num)
#         return craft_list, error_list

#     def get_from_craft_lists(self, craft_list, secondary_craft_list, num):
#         n = num - len(craft_list)
#         if n < len(secondary_craft_list):
#             for i in range(n):
#                 craft_list.append(secondary_craft_list[i])
#         else:
#             for i in range(len(secondary_craft_list)):
#                 craft_list.append(secondary_craft_list[i])
#         return craft_list

#     def get_gph(self, item_value, sales_list=None, error_list=None):
#         new_error_list = []
#         if type(item_value) == tuple:
#             item_value = item_value[0]
#         transaction_list = Transaction.query.filter_by(item_value=item_value, user_id=get_user_id()).all()
#         if sales_list is None:
#             sales_list = [x for x in transaction_list if (x.gil_value > 0 and x.amount < 0)]
#         restock_list = [x for x in transaction_list if (x.gil_value == 0 and x.amount > 0)]

#         if len(sales_list) > 0 and len(restock_list) > 0:
#             deltas = []
#             for x in sales_list:
#                 matching_restock = self.match_stock(x.time, restock_list)
#                 if matching_restock is not None:
#                     deltas.append(convert_string_to_datetime(matching_restock.time) - convert_string_to_datetime(x.time))
#                     restock_list.remove(matching_restock)
#             if len(deltas) > 0:
#                 total_time = timedelta()
#                 for x in deltas:
#                     total_time += x
#                 avg_time = total_time / len(deltas)
#                 if error_list is None:
#                     return floor(self.get_profit(item_value)[0] / (avg_time.days * 24 + avg_time.seconds / 3600))
#                 else:
#                     profit = self.get_profit(item_value)
#                     new_error_list = profit[1]
#                     profit = profit[0]
#                     return [
#                         floor(profit / (avg_time.days * 24 + avg_time.seconds / 3600)),
#                         error_list + new_error_list,
#                     ]
#         return None

#     def match_stock(self, sale_time, restock_list):
#         sale_time = convert_string_to_datetime(sale_time)
#         for x in restock_list:
#             if convert_string_to_datetime(x.time) < sale_time:
#                 # time_gap = sale_time - x
#                 # TODO option here to disregard matches with a time gap longer than n
#                 return x
#         return None

#     def get_profit(self, item_value, error_list=None):
#         new_error_list = []
#         new_item_value = None
#         if isinstance(item_value, tuple):
#             new_item_value = item_value[0]
#         else:
#             new_item_value = item_value
#         avg = self.get_average_price(new_item_value, mode="s")
#         result = self.get_crafting_cost(new_item_value, new_error_list)
#         cost = result[0]
#         if avg is None:
#             avg = 0
#         if cost is None:
#             print("{} has a crafting cost of None, setting to 0".format(new_item_value))
#             cost = 0
#         if error_list is not None:
#             new_error_list = result[1]
#             return [avg - cost, error_list + new_error_list]
#         else:
#             return [avg - cost, new_error_list]

#     def get_average_price(self, item_value, mode=None):
#         price_list = []
#         transaction_list = Transaction.query.filter_by(item_value=item_value, user_id=self.user_id).all()
#         if len(transaction_list) > 0:
#             if mode is None:
#                 price_list = [x.gil_value for x in transaction_list if x.gil_value != 0]
#             elif mode == "sale" or mode == "sales" or mode == 1 or mode == "s":
#                 price_list = [x.gil_value for x in transaction_list if x.gil_value > 0]
#             elif mode == "purchase" or mode == "purchases" or mode == -1 or mode == "p":
#                 price_list = [x.gil_value * -1 for x in transaction_list if x.gil_value < 0]
#             else:
#                 print("Invalid mode passed to get_average_price")

#         if len(price_list) > 4:
#             return sum(price_list) / len(price_list)
#         else:
#             # pull from Universalis
#             # first, send get request to universalis for the item ID and the user's world
#             # right now this will only get the first profile of a user, I need a way to reorder them or something
#             world = Profile.query.filter_by(user_id=current_user.id).first().world
#             response = req.get(f"https://universalis.app/api/{world}/11975")
#             # retrieve listings
#             # iterate through the first x listings (where x is either hard-coded or a % of total listings)
#             return None

#     def get_crafting_cost(self, item_value, error_list=None):
#         item = get_item(item_value)
#         if error_list is None:
#             error_list = []
#         if item.recipes != None:
#             # right now this will double-count the cost of products with more than 1 recipe
#             craft_cost = 0
#             recipe_list = [x.id for x in item.recipes]
#             for recipe in recipe_list:
#                 recipe = Recipe.query.get(recipe)
#                 for comp in recipe.components:
#                     result = self.get_crafting_cost(comp.item_value, error_list)
#                     if result is None:
#                         error_list.append("Component {} returned None for crafting cost".format(comp.item_value))
#                     else:
#                         comp_cost = result[0]
#                         error_list = result[1]
#                         craft_cost += comp_cost
#             return [craft_cost, error_list]
#         else:
#             craft_cost = self.get_average_price(item_value, mode="p")
#             if craft_cost is None:
#                 error_list.append("{} has None for craft_cost, setting to 0".format(item_value))
#                 craft_cost = 0
#             return [craft_cost, error_list]




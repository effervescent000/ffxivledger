from datetime import timedelta, datetime
from math import floor
from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app, jsonify
from flask_login import current_user
import flask_praetorian as fp
import requests as req
# from flask_cors import CORS

from . import db
from .models import Item, Stock, Recipe, Component, Profile, ItemStats, User
from .utils import convert_string_to_datetime, convert_to_time_format, get_item

bp = Blueprint("crafting", __name__, url_prefix="/craft")
# CORS(bp)

@bp.route("/get_queue/<amount>", methods=["GET"])
@fp.auth_required
def get_queue(amount):
    user_id = fp.current_user().id
    queue = Queue(amount, user_id)
    full_queue = queue.generate_queue()
    short_queue = []
    while len(short_queue) < int(amount):
        short_queue.append(full_queue.pop(0))
    return jsonify(short_queue)


def generate_warnings(queue):
    # iterate over each item in queue
    for item in queue:
        # for each item, get its recipe and drill down to figure out the 
        pass


def get_item_stats(world_id, item_id):
        item_stats = ItemStats.query.filter_by(world_id=world_id, item_id=item_id).first()
        if item_stats == None:
            item_stats = ItemStats(world_id=world_id, item_id=item_id)
            db.session.add(item_stats)
            db.session.commit()
        return item_stats

class Queue:
    def __init__(self, num, user_id):
        self.num = num
        # self.user_id = user_id
        self.profile = User.query.get(user_id).get_active_profile()
    
    # method to iterate over recipes in DB and find the highest gil/hour ones to craft
    def generate_queue(self):
        queue = []
        # for now just do all jobs but I would like to make it so you can pick one or a couple or w/e
        for recipe in Recipe.query.all():
            # exclude items that are in stock already
            stock = Stock.query.filter_by(item_id=recipe.item_id, profile_id=self.profile.id).first()
            if stock == None or stock.amount == 0:
                # only include top-level craftables (nothing that's a component of something else)
                # (this isn't perfect b/c it excludes certain pieces of gear but I'll figure that out later)
                if Component.query.filter_by(item_id=recipe.item_id).first() == None:
                    if recipe.job == "ALC":
                        if self.profile.alc_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
                    elif recipe.job == "ARM":
                        if self.profile.arm_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
                    elif recipe.job == "BSM":
                        if self.profile.bsm_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
                    elif recipe.job == "CRP":
                        if self.profile.crp_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
                    elif recipe.job == "CUL":
                        if self.profile.cul_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
                    elif recipe.job == "GSM":
                        if self.profile.gsm_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
                    elif recipe.job == "LTW":
                        if self.profile.ltw_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
                    elif recipe.job == "WVR":
                        if self.profile.wvr_level >= recipe.level:
                            queue.append({
                                "name": recipe.item.name,
                                "id": recipe.item.id,
                                "gph": self.get_gph(Item.query.get(recipe.item_id))
                            })
        queue.sort(reverse=True, key=lambda x : x["gph"])
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
            item_stats = get_item_stats(self.profile.world_id, item.id)
            return item_stats.price

    # method to check freshness of queried data and requery if necessary
    def check_cached_data(self, item):
        # first check when stats_updated was last updated, if > 12hrs ago, requery
        # grab stats_updated and convert to a date if it's valid
        now = datetime.now()
        item_stats = get_item_stats(self.profile.world_id, item.id)
        if item_stats.stats_updated != None:
            last_update = convert_string_to_datetime(item_stats.stats_updated)
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
        profile_world = self.profile.world_id
        data = req.get(f"https://universalis.app/api/{profile_world}/{item.id}").json()
        # if world data is below a certain # of listings, then grab datacenter data
        item_stats = get_item_stats(profile_world, item.id)
        if len(data.get("listings")) <= 3:
            # overwrite data with dc data for given item
            data = req.get(f"https://universalis.app/api/{self.profile.world.datacenter.name}/{item.id}").json()
            # now update item stats
            item_stats.stats_updated = convert_to_time_format(datetime.now())
            item_stats.price = data.get("averagePrice")
            item_stats.sales_velocity = data.get("regularSaleVelocity")
            db.session.commit()
        else:
            # instead of using averagePrice, use minPrice (only with world data, continue using averagePrice for DC data)
            item_stats.stats_updated = convert_to_time_format(datetime.now())
            item_stats.price = data.get("minPrice")
            item_stats.sales_velocity = data.get("regularSaleVelocity")
            db.session.commit()
        # include checks for vanity items (does it require lvl 1 to use?), if so then do not pay attention to NQ vs HQ
        # if it's an actual gear item, then preferentially use HQ data sources when available

        # now update crafting cost
        crafting_cost = 0
        # first, check if an item has any recipes (items that can't be crafted will have None crafting cost)
        if len(item.recipes) > 0:
            # if it does, then get its crafting cost
            # doing it in a for loop like this will cause the crafting cost of certain items to be doubled (or tripled or w/e)
            for recipe in item.recipes:
                for component in recipe.components:
                    component_stats = get_item_stats(profile_world, component.item.id)
                    # don't drill all the way down, just go 1 level
                    # use whichever is cheaper, the cost to craft or buy the components
                    if component_stats.craft_cost == None:
                        crafting_cost += component_stats.price * component.item_quantity
                    else:
                        crafting_cost += component_stats.price if component_stats.price <= component_stats.craft_cost else component_stats.craft_cost
            # don't generate any warnings or anything here, just assign it to the itemstats model
            item_stats.craft_cost = crafting_cost


    # method to estimate profit/hour
    def get_gph(self, item):
        # first, get crafting cost
        crafting_cost = self.get_crafting_cost(item)
        print(f"{item.name} costs {crafting_cost} gil to make")
        # next, retrieve sale value of finished product
        self.check_cached_data(item)
        item_stats = get_item_stats(self.profile.world_id, item.id)
        profit = item_stats.price - crafting_cost
        # return: multiply profit by sale velocity HQ (which I believe is calculated per day)
        return round((profit * item_stats.sales_velocity) / 24)

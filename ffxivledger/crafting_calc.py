from datetime import timedelta, datetime
from flask import Blueprint, jsonify, request
import flask_praetorian as fp
import requests as req

from . import db
from .models import Item, Stock, Recipe, Component, ItemStats, World, Skip
from .schema import ItemStatsSchema
from .utils import convert_string_to_datetime, convert_to_time_format

bp = Blueprint("crafting", __name__, url_prefix="/craft")

one_itemstats_schema = ItemStatsSchema()
multi_itemstats_schema = ItemStatsSchema(many=True)

# how many hours old data can be while still being considered fresh
freshness_threshold = 6
max_updates = 75


@bp.route("/get_queue/<amount>", methods=["GET"])
@fp.auth_required
def get_queue(amount):
    profile = fp.current_user().get_active_profile()
    queue = Queue(profile)
    full_queue = queue.generate_queue()
    short_queue = []
    while len(short_queue) < int(amount):
        short_queue.append(full_queue.pop(0))
    return jsonify(short_queue)


@bp.route("/alerts/<world_id>-<item_id>", methods=["GET"])
def generate_warnings(world_id, item_id):
    warning_list = []
    # iterate over each item in queue
    item = Item.query.get(item_id)
    # if an item has recipes, then iterate over them (or maybe just grab the first one?)
    if len(item.recipes) > 0:
        # iterate over the component items in each recipe to see if there are any where the price is less than the crafting cost
        for recipe in item.recipes:
            for component in recipe.components:
                comp_stats = get_item_stats(world_id, component.item_id)
                if comp_stats.craft_cost != None:
                    if comp_stats.price <= comp_stats.craft_cost:
                        warning_list.append(
                            {
                                "name": component.item.name,
                                "crafting_cost": comp_stats.craft_cost,
                                "price": comp_stats.price,
                            }
                        )
    return jsonify(warning_list)


def get_item_stats(world_id, item_id):
    item_stats = ItemStats.query.filter_by(world_id=world_id, item_id=item_id).first()
    if item_stats == None:
        item_stats = ItemStats(world_id=world_id, item_id=item_id)
        db.session.add(item_stats)
        db.session.commit()
    return item_stats


# @bp.route("/stats/update/<world_id>", methods=["PUT"])
# def force_update_stats(world):
#     if type(world) is int:
#         world = World.query.get(world)
#     item_stats = ItemStats.query.filter_by(world_id=world).all()
#     for x in item_stats:
#         update_cached_data(x, world)


@bp.route("/stats/update", methods=["PUT"])
def update_world_data():
    # all this expects to take in is a world ID so like {"id": 62} for Diabolos
    data = request.get_json()
    world = World.query.get(data.get("id"))
    item_stats_list = ItemStats.query.filter_by(world_id=world.id).all()
    item_list = Item.query.all()
    if len(item_stats_list) < len(item_list):
        for item in item_list:
            if ItemStats.query.filter_by(world_id=world.id, item_id=item.id).first() == None:
                item_stats = ItemStats(item_id=item.id, world_id=world.id)
                db.session.add(item_stats)
                db.session.commit()
                update_cached_data(item, world)
        item_stats_list = ItemStats.query.filter_by(world_id=world.id).all()
    item_stats_list.sort(key=lambda x: convert_string_to_datetime(x.stats_updated))
    update_counter = 0
    updated_items_stats = []
    while update_counter < max_updates:
        item = item_stats_list[0]
        if item.stats_updated != None:
            last_update = convert_string_to_datetime(item.stats_updated)
            if (datetime.now() - last_update).total_seconds() / 3600 < freshness_threshold:
                # data no longer needs to be refreshed if this condition is triggered so break out of the while loop
                break
            else:
                update_cached_data(item.item, world)
                updated_items_stats.append(item_stats_list.pop(0))
                update_counter += 1
        else:
            # if the data has never been updated, update w/o counting it against the total updates
            update_cached_data(item.item, world)
            updated_items_stats.append(item_stats_list.pop(0))

    return jsonify(multi_itemstats_schema.dump(updated_items_stats))


# function to actually query universalis
def update_cached_data(item, world):
    # first, get world data as normal
    data = req.get(f"https://universalis.app/api/{world.id}/{item.id}").json()
    # if world data is below a certain # of listings, then grab datacenter data
    print(f"Updating item {item.name}")
    item_stats = get_item_stats(world.id, item.id)
    if len(data.get("listings")) <= 3:
        # overwrite data with dc data for given item
        data = req.get(f"https://universalis.app/api/{world.datacenter.name}/{item.id}").json()
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
                component_stats = get_item_stats(world.id, component.item.id)
                # don't drill all the way down, just go 1 level
                # use whichever is cheaper, the cost to craft or buy the components
                if component_stats.price == None:
                    update_cached_data(component.item, world)
                if component_stats.craft_cost == None:
                    crafting_cost += component_stats.price * component.item_quantity
                else:
                    crafting_cost += (
                        component_stats.price
                        if component_stats.price <= component_stats.craft_cost
                        else component_stats.craft_cost
                    )
        # don't generate any warnings or anything here, just assign it to the itemstats model
        item_stats.craft_cost = crafting_cost
        db.session.commit()


class Queue:
    def __init__(self, profile):
        self.profile = profile
        self.update_counter = 0
        self.max_updates = 75
        self.queue = []
        # how many hours old data can be while still being fresh
        self.freshness_threshold = 6

    def build_item_stats_list(self, item_list):
        item_stats_list = ItemStats.query.filter_by(world_id=self.profile.world.id).all()
        if len(item_stats_list) < len(item_list):
            for item in item_list:
                if ItemStats.query.filter_by(world_id=self.profile.world.id, item_id=item.id).first() == None:
                    item_stats = ItemStats(item_id=item.id, world_id=self.profile.world.id)
                    db.session.add(item_stats)
                    db.session.commit()
                    update_cached_data(item, self.profile.world)
        item_stats_list = ItemStats.query.filter_by(world_id=self.profile.world.id).all()
        # print(item_stats_list)
        return item_stats_list

    # method to iterate over recipes in DB and find the highest gil/hour ones to craft
    def generate_queue(self):
        # pull up the itemstats and pass them to the update method
        # item_stats_list = self.build_item_stats_list(Item.query.all())
        # self.update_data(item_stats_list)
        # for now just do all jobs but I would like to make it so you can pick one or a couple or w/e
        for recipe in Recipe.query.all():
            # ensure the item is not set to be skipped by the user
            if len(recipe.item.skips) > 0:
                # if there are any skips, then query to see if there's one that matches the profile
                skip_query = Skip.query.filter_by(item_id=recipe.item_id, profile_id=self.profile.id).first()
                if skip_query == None:
                    self.process_recipe(recipe)
                # check to see if the skip has expired, if so, remove it from the db
                else:
                    skip_timestamp = convert_string_to_datetime(skip_query.time)
                    # if it's been more than 24 hrs, remove the skip
                    if (datetime.now() - skip_timestamp).total_seconds() / 3600 > 24:
                        db.session.delete(skip_query)
                        db.session.commit()
            else:
                self.process_recipe(recipe)
        self.queue.sort(reverse=True, key=lambda x: x["gph"])
        return self.queue

    def make_queue_item(self, recipe):
        item_stats = get_item_stats(self.profile.world.id, recipe.item.id)
        item_dict = {
            "name": recipe.item.name,
            "id": recipe.item.id,
            "gph": self.get_gph(Item.query.get(recipe.item_id), item_stats),
            "craft_cost": item_stats.craft_cost,
        }
        return item_dict

    def process_recipe(self, recipe):
        # exclude items that are in stock already
        stock = Stock.query.filter_by(item_id=recipe.item_id, profile_id=self.profile.id).first()
        if stock == None or stock.amount == 0:
            # only include top-level craftables (nothing that's a component of something else)
            # (this isn't perfect b/c it excludes certain pieces of gear but I'll figure that out later)
            if Component.query.filter_by(item_id=recipe.item_id).first() == None:
                if recipe.job == "ALC":
                    if self.profile.alc_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))
                elif recipe.job == "ARM":
                    if self.profile.arm_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))
                elif recipe.job == "BSM":
                    if self.profile.bsm_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))
                elif recipe.job == "CRP":
                    if self.profile.crp_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))
                elif recipe.job == "CUL":
                    if self.profile.cul_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))
                elif recipe.job == "GSM":
                    if self.profile.gsm_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))
                elif recipe.job == "LTW":
                    if self.profile.ltw_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))
                elif recipe.job == "WVR":
                    if self.profile.wvr_level >= recipe.level:
                        self.queue.append(self.make_queue_item(recipe))

    # method to calculate crafting cost recursively
    def get_crafting_cost(self, item):
        # first, declare crafting cost variable
        crafting_cost = 0
        # next, check if the item can be crafted
        if len(item.recipes) > 0:
            for recipe in item.recipes:
                # iterate through the components of each recipe to get their individual crafting cost
                for component in recipe.components:
                    crafting_cost += self.get_crafting_cost(component.item) * component.item_quantity
                # this cuts off after the first recipe
                return crafting_cost / recipe.item_quantity

        else:
            # if no, query Universalis and get the going rate of the material, return this
            item_stats = get_item_stats(self.profile.world.id, item.id)
            # if self.update_counter < self.max_updates:
            #     self.check_cached_data(item, item_stats)
            # always update if there's no data at all
            if item_stats.price == None:
                update_cached_data(item, self.profile.world)
            return item_stats.price

    # method to check freshness of queried data and requery if necessary
    # def check_cached_data(self, item, item_stats):
    #     # first check when stats_updated was last updated, if > 12hrs ago, requery
    #     # grab stats_updated and convert to a date if it's valid
    #     if item_stats.stats_updated != None:
    #         last_update = convert_string_to_datetime(item_stats.stats_updated)
    #         # if it's been more than 6 hours:
    #         if (datetime.now() - last_update).total_seconds() / 3600 > self.freshness_threshold:
    #             # print(f"I think it's been more than {self.freshness_threshold} hrs, updating data for {item.name}")
    #             self.update_counter += 1
    #             update_cached_data(item, self.profile.world)
    #     else:
    #         # print(f"No data for {item.name}, updating...")
    #         self.update_counter += 1
    #         update_cached_data(item, self.profile.world)

    def update_data(self, item_stats_list):
        # sort item_stats_list, oldest data first
        # iterate through item_stats_list and update each element, until either:
        # 1) the oldest item is still "fresh", or
        # 2) the update counter maxes out
        item_stats_list.sort(key=lambda x: convert_string_to_datetime(x.stats_updated))
        # print(item_stats_list[0].stats_updated)
        while self.update_counter < self.max_updates:
            if item_stats_list[0].stats_updated != None:
                last_update = convert_string_to_datetime(item_stats_list[0].stats_updated)
                print(f"Last update for {item_stats_list[0].item.name} was at {last_update}")
                if (datetime.now() - last_update).total_seconds() / 3600 < self.freshness_threshold:
                    break
                else:
                    update_cached_data(item_stats_list[0].item, self.profile.world)
                    item_stats_list.pop(0)
                    self.update_counter += 1
            else:
                update_cached_data(item_stats_list[0].item, self.profile.world)
                item_stats_list.pop(0)

    # method to estimate profit/hour
    def get_gph(self, item, item_stats=None):
        # first, get crafting cost
        crafting_cost = self.get_crafting_cost(item)
        # print(f"{item.name} costs {crafting_cost} gil to make")
        # next, retrieve sale value of finished product
        if item_stats == None:
            item_stats = get_item_stats(self.profile.world.id, item.id)
        # if self.update_counter < self.max_updates:
        #     self.check_cached_data(item, item_stats)
        if item_stats.price == None:
            # always update if there's no data for this item
            update_cached_data(item, self.profile.world)
        profit = item_stats.price - crafting_cost
        # return: multiply profit by sale velocity HQ (which I believe is calculated per day)
        return round((profit * item_stats.sales_velocity) / 24)

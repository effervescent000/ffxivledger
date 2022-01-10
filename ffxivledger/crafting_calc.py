import os
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
# freshness_threshold = int(os.environ['FRESHNESS_THRESHOLD'])
# max_updates = int(os.environ['MAX_UPDATES'])


@bp.route("/get", methods=['GET'])
@fp.auth_required
def get_crafts():
    profile = fp.current_user().get_active_profile()
    # get all recipes
    master_query = Recipe.query.all()
    recipes = [x for x in master_query]
    # iterate over recipes
    for recipe in master_query:
        # check if the recipe is used in another recipe, if so remove it so we are only crafting top-level stuff (maybe add this as an option at some point)
        if Component.query.filter_by(item_id=recipe.item_id).first() != None:
            # print(f"Removing {recipe.item.name} for from recipe list")
            recipes.remove(recipe)
            continue
        # check if the recipe is set to be skipped, if so remove it from the list
        if len(recipe.item.skips) > 0:
            skip_query = Skip.query.filter_by(item_id=recipe.item_id, profile_id=profile.id).first()
            if skip_query != None:
                # check to see if the skip has expired
                skip_timestamp = convert_string_to_datetime(skip_query.time)
                # if it's been more than 24 hrs, remove the skip. if not, remove the recipe from the list
                if (datetime.now() - skip_timestamp).total_seconds() / 3600 > 24:
                    db.session.delete(skip_query)
                    db.session.commit()
                else:
                    recipes.remove(recipe)
                    continue
        # check if the active profile can even craft it
        if recipe.job == "ALC":
            if profile.alc_level < recipe.level:
                recipes.remove(recipe)
                continue
        elif recipe.job == "ARM":
            if profile.arm_level < recipe.level:
                recipes.remove(recipe)
                continue
        elif recipe.job == "BSM":
            if profile.bsm_level < recipe.level:
                recipes.remove(recipe)
                continue
        elif recipe.job == "CRP":
            if profile.crp_level < recipe.level:
                recipes.remove(recipe)
                continue
        elif recipe.job == "CUL":
            if profile.cul_level < recipe.level:
                recipes.remove(recipe)
                continue
        elif recipe.job == 'GSM':
            if profile.gsm_level < recipe.level:
                recipes.remove(recipe)
                continue
        elif recipe.job == "LTW":
            if profile.ltw_level < recipe.level:
                recipes.remove(recipe)
                continue
        elif recipe.job == 'WVR':
            if profile.wvr_level < recipe.level:
                recipes.remove(recipe)
                continue
        # check if the item is already in stock
        stock = Stock.query.filter_by(item_id=recipe.item_id, profile_id=profile.id).first()
        if stock != None and stock.amount > 0:
            recipes.remove(recipe)
            continue
    # i think that's all the conditions i want to check for here
    # once we're done removing stuff from the list, create a new list with the itemstats and return that
    item_stats_list = [ItemStats.query.filter_by(item_id=x.item_id, world_id=profile.world.id).first() for x in recipes]
    return jsonify(multi_itemstats_schema.dump(item_stats_list))


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


@bp.route("/card/<world_id>-<item_id>", methods=["GET"])
def generate_card(world_id, item_id):
    warning_list = []
    # iterate over each item in queue
    item = Item.query.get(item_id)
    # if an item has recipes, then iterate over them (or maybe just grab the first one?)
    if len(item.recipes) > 0:
        # iterate over the component items in each recipe to see if there are any where the price is less than the crafting cost
        for recipe in item.recipes:
            for component in recipe.components:
                comp_stats = get_item_stats(world_id, component.item_id)
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
# prob rename this to like... prep_world_data or something?
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
    # now we prep the list for the bulk update function
    # start by slicing the list from the start until the end OR until max_updates, whichever is lower
    max_updates = int(os.environ['MAX_UPDATES'])
    if len(item_stats_list) > max_updates:
        item_stats_list = item_stats_list[:max_updates]
    # check the last item in the list, if it's within the freshness threshold, 
    # then create a new list which only includes items outside the freshness threshold (list comprehension?)
    freshness_threshold = int(os.environ['FRESHNESS_THRESHOLD'])
    if (datetime.now() - convert_string_to_datetime(item_stats_list[-1].stats_updated)).total_seconds() / 3600 < freshness_threshold:
        item_stats_list = [x for x in item_stats_list if (datetime.now() - convert_string_to_datetime(x.stats_updated)).total_seconds() / 3600 < freshness_threshold]
    # once all this is done, pass the list to the update function
    # update_bulk_data(item_stats_list, world)
    return jsonify(multi_itemstats_schema.dump(update_bulk_data(item_stats_list, world)))


def update_bulk_data(item_stats_list, world):
    """Takes in a list of items stats and queries universalis, then updates each of the provided items"""
    item_id_list = ",".join([str(x.item_id) for x in item_stats_list])
    item_data = req.get(f"https://universalis.app/api/{world.id}/{item_id_list}").json().get("items")
    # iterate over the items in the data
    # for now just copy the methodology ive been using of get the DC data instead if there aren't enough listings
    # create a list to add items to that dont have enough world info
    # at the end we'll send another query to universalis for the DC data of the items in this list
    items_to_requery = []
    # go down the items in the item_data results
    updated_items = []
    for item in item_data:
        # if it has enough listings, then pass that data to process_item_data, along with the world id
        if len(item.get("listings")) >= 3:
            updated_items.append(process_item_data(item, world.id))
        # if not, add it to items_to_requery
        else:
            items_to_requery.append(item)
    # after the above iteration, repeat the process with items_to_requery
    if len(items_to_requery) == 1:
        item = req.get(f"https://universalis.app/api/{world.datacenter.name}/{item_id_list}").json()
        updated_items.append(process_item_data(item, world.id))
    elif len(items_to_requery) > 1:
        item_id_list = ",".join([str(x.get("itemID")) for x in items_to_requery])
        item_data = req.get(f"https://universalis.app/api/{world.datacenter.name}/{item_id_list}").json().get("items")
        for item in item_data:
            updated_items.append(process_item_data(item, world.id))
    return updated_items

def process_item_data(item_json, world_id):
    item_stats = ItemStats.query.filter_by(item_id=item_json.get("itemID"), world_id=world_id).first()
    item_stats.stats_updated = convert_to_time_format(datetime.now())
    item_stats.price = item_json.get("minPrice") if item_json.get("worldID") != None else item_json.get("averagePrice")
    item_stats.sales_velocity = item_json.get("regularSaleVelocity")
    db.session.commit()
    return item_stats


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


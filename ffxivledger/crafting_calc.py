import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
import requests as req

from . import db
from .models import Item, Stock, Recipe, Component, ItemStats, World, Skip
from .schema import ItemStatsSchema
from .utils import convert_string_to_datetime, convert_to_time_format

bp = Blueprint("crafting", __name__, url_prefix="/craft")

one_itemstats_schema = ItemStatsSchema()
multi_itemstats_schema = ItemStatsSchema(many=True)


@bp.route("/get", methods=["GET"])
@jwt_required()
def get_crafts():
    profile = current_user.get_active_profile()

    alc_recipes = Recipe.query.filter(Recipe.job == "ALC", Recipe.level <= profile.alc_level).all()
    arm_recipes = Recipe.query.filter(Recipe.job == "ARM", Recipe.level <= profile.arm_level).all()
    bsm_recipes = Recipe.query.filter(Recipe.job == "BSM", Recipe.level <= profile.bsm_level).all()
    crp_recipes = Recipe.query.filter(Recipe.job == "CRP", Recipe.level <= profile.crp_level).all()
    cul_recipes = Recipe.query.filter(Recipe.job == "CUL", Recipe.level <= profile.cul_level).all()
    gsm_recipes = Recipe.query.filter(Recipe.job == "GSM", Recipe.level <= profile.gsm_level).all()
    ltw_recipes = Recipe.query.filter(Recipe.job == "LTW", Recipe.level <= profile.ltw_level).all()
    wvr_recipes = Recipe.query.filter(Recipe.job == "WVR", Recipe.level <= profile.wvr_level).all()

    master_query = (
        alc_recipes + arm_recipes + bsm_recipes + crp_recipes + cul_recipes + gsm_recipes + ltw_recipes + wvr_recipes
    )

    recipes = [x for x in master_query]
    for recipe in master_query:
        # check if the recipe is used in another recipe, if so remove it so we are only crafting top-level stuff (maybe add this as an option at some point)
        if Component.query.filter_by(item_id=recipe.item_id).first() != None:
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
        # check if the item is already in stock
        stock = Stock.query.filter_by(item_id=recipe.item_id, profile_id=profile.id).first()
        if stock != None and stock.amount > 0:
            recipes.remove(recipe)
            continue
    # once we're done removing stuff from the list, create a new list with the itemstats and return that
    item_stats_list = [
        ItemStats.query.filter_by(item_id=x.item_id, world_id=profile.world.id).first() for x in recipes
    ]
    return jsonify(multi_itemstats_schema.dump(item_stats_list))


@bp.route("/card/<world_id>-<item_id>", methods=["GET"])
def generate_card(world_id, item_id):
    world_id = int(world_id)
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
    if type(world_id) == int and type(item_id) == int:
        item_stats = ItemStats.query.filter_by(world_id=world_id, item_id=item_id).first()
        if item_stats == None:
            item_stats = ItemStats(world_id=world_id, item_id=item_id)
            db.session.add(item_stats)
            db.session.commit()
        return item_stats
    print("world_id", world_id, type(world_id))
    print("item_id", item_id, type(item_id))
    raise TypeError(f"Invalid arguments and passed to get_item_stats")


@bp.route("/stats/update", methods=["PUT"])
# prob rename this to like... prep_world_data or something?
def update_world_data():
    # all this expects to take in is a world ID so like {"id": 62} for Diabolos
    data = request.get_json()
    world = World.query.get(data.get("id"))
    item_stats_list = ItemStats.query.filter_by(world_id=world.id).all()
    item_list = Item.query.all()
    if len(item_stats_list) < len(item_list):
        items_to_add = []
        for item in item_list:
            if ItemStats.query.filter_by(world_id=world.id, item_id=item.id).first() == None:
                items_to_add.append(item.id)
        update_bulk_data(items_to_add, world)
        item_stats_list = ItemStats.query.filter_by(world_id=world.id).all()
    item_stats_list.sort(key=lambda x: convert_string_to_datetime(x.stats_updated))
    # now we prep the list for the bulk update function
    # start by slicing the list from the start until the end OR until max_updates, whichever is lower
    max_updates = int(os.environ["MAX_UPDATES"])
    item_stats_lists_list = []
    if len(item_stats_list) > max_updates:
        item_stats_list = item_stats_list[:max_updates]
        item_stats_lists_list = process_item_stats_list(item_stats_list)
    # check the last item in the list, if it's within the freshness threshold,
    # then create a new list which only includes items outside the freshness threshold (list comprehension?)
    freshness_threshold = int(os.environ["FRESHNESS_THRESHOLD"])
    updated_items_stats = []
    for i_s_l in item_stats_lists_list:
        last_updated = convert_string_to_datetime(i_s_l[-1].stats_updated)
        if (datetime.now() - last_updated).total_seconds() / 3600 < freshness_threshold:
            i_s_l = [
                x
                for x in item_stats_list
                if (datetime.now() - convert_string_to_datetime(x.stats_updated)).total_seconds() / 3600
                < freshness_threshold
            ]
        # once all this is done, pass the list to the update function
        # update_bulk_data(item_stats_list, world)
        item_id_list = ",".join([str(x.item_id) for x in i_s_l])
        updated_items_stats += update_bulk_data(item_id_list, world)
        for item_stats in updated_items_stats:
            if item_stats.craft_cost == None:
                item_stats.craft_cost = get_crafting_cost(item_stats.item, world.id)
                db.session.commit()

    return jsonify(multi_itemstats_schema.dump(updated_items_stats))


def process_item_stats_list(item_stats_list):
    item_stats_lists_list = []
    while len(item_stats_list) / 100 > 1:
        item_stats_lists_list.append(item_stats_list[:100])
        item_stats_list = item_stats_list[100:]
    item_stats_lists_list.append(item_stats_list)
    return item_stats_lists_list


def update_bulk_data(item_id_list, world):
    """Takes in a list of items stats and queries universalis, then updates each of the provided items"""
    item_data = req.get(f"https://universalis.app/api/{world.id}/{item_id_list}").json().get("items")
    items_to_requery = []
    updated_items_stats = []
    for item in item_data:
        # if it has enough listings, then pass that data to process_item_data, along with the world id
        if len(item.get("listings")) >= 3:
            updated_items_stats.append(process_item_data(item, world.id))
        # if not, add it to items_to_requery
        else:
            items_to_requery.append(item)
    # after the above iteration, repeat the process with items_to_requery
    if len(items_to_requery) == 1:
        item_id = items_to_requery[0].get("itemID")
        item = req.get(f"https://universalis.app/api/{world.datacenter.name}/{item_id}").json()
        updated_items_stats.append(process_item_data(item, world.id))
    elif len(items_to_requery) > 1:
        item_id_list = ",".join([str(x.get("itemID")) for x in items_to_requery])
        item_data = req.get(f"https://universalis.app/api/{world.datacenter.name}/{item_id_list}").json().get("items")
        for item in item_data:
            updated_items_stats.append(process_item_data(item, world.id))
    return updated_items_stats


def process_item_data(item_json, world_id):
    item_id = item_json.get("itemID")
    item_stats = get_item_stats(world_id, item_id)
    item_stats.stats_updated = convert_to_time_format(datetime.now())
    item_stats.price = item_json.get("minPrice") if item_json.get("worldID") != None else item_json.get("averagePrice")
    item_stats.sales_velocity = item_json.get("regularSaleVelocity")
    db.session.commit()

    # now update crafting cost
    # item_stats.craft_cost = get_crafting_cost(item_stats.item, world_id)
    # db.session.commit()

    return item_stats


def get_crafting_cost(item, world_id):
    crafting_cost = 0

    if len(item.recipes) > 0:
        # if it does, then get its crafting cost
        # doing it in a for loop like this will cause the crafting cost of certain items to be doubled (or tripled or w/e)
        for recipe in item.recipes:
            for component in recipe.components:
                component_stats = get_item_stats(world_id, component.item.id)
                # don't drill all the way down, just go 1 level
                # use whichever is cheaper, the cost to craft or buy the components
                if component_stats.price == None:
                    return None
                if component_stats.craft_cost == None:
                    crafting_cost += component_stats.price * component.item_quantity
                else:
                    crafting_cost += (
                        component_stats.price
                        if component_stats.price <= component_stats.craft_cost
                        else component_stats.craft_cost
                    )
    return crafting_cost if crafting_cost > 0 else None

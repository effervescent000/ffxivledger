from flask import Blueprint, request, jsonify, current_app
import requests as req

from . import db
from .models import World, Datacenter
from .schema import WorldSchema, DatacenterSchema

bp = Blueprint("world", __name__, url_prefix="/world")

one_world_schema = WorldSchema()
multi_world_schema = WorldSchema(many=True)

@bp.route("/add", methods=['POST'])
def add_world_by_name():
    data = request.get_json()
    world_name = data.get("name")
    # search XIVAPI to get the world id from its name
    search = req.get(f'https://xivapi.com/search?indexes=World&string={world_name}&private_key={current_app.config.get("XIVAPI_KEY")}').json()
    results = search.get("Results")
    world_id = None
    if len(results) > 1:
        for result in results:
            if world_name.lower() == result.get("Name").lower():
                world_id = result.get("ID")
    elif len(results) == 1:
        world_id = results[0].get("ID")
    else:
        # if no match is found, then return error
        return jsonify("No results found in XIVAPI search")

    world = World.query.get(world_id)
    if world == None:
        # GET request for world id
        world_data = req.get(f"https://xivapi.com/World/{world_id}").json()
        # populate world data from the response
        dc_data = world_data.get("DataCenter")
        dc_id = dc_data.get("ID")
        if Datacenter.query.get(dc_id) == None:
            dc = Datacenter(id=dc_id, name=dc_data.get("Name"))
            db.session.add(dc)
            db.session.commit()
        world = World(id=world_id, name=world_name, datacenter_id=dc_id)
        db.session.add(world)
        db.session.commit()
    return jsonify(one_world_schema.dump(world))


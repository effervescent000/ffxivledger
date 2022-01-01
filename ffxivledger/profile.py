from flask import Blueprint, request, jsonify
import flask_praetorian as fp

from . import db
from .models import User, Profile, World, Retainer
from .schema import UserSchema, ProfileSchema

bp = Blueprint("profile", __name__, url_prefix="/profile")

one_profile_schema = ProfileSchema()
multi_profile_schema = ProfileSchema(many=True)


@bp.route("/add", methods=["POST"])
@fp.auth_required
def add_profile():
    user_id = fp.current_user().id
    data = request.get_json()
    print(data)
    world = data.get("world")
    if world == None:
        return jsonify("Must include a world")
    # check if the current_user also has a profile on this world, if so reject
    # query = ProfileList.query.filter_by(user_id=user_id).first()

    query = Profile.query.filter_by(user_id=user_id, world_id=world).first()
    if query != None:
        return jsonify(f"Profile already exists on world {world}")

    # check each job level, if any are not included then set them to 0 and add them to profile
    alc_level = data.get("alc_level")
    arm_level = data.get("arm_level")
    bsm_level = data.get("bsm_level")
    crp_level = data.get("crp_level")
    cul_level = data.get("cul_level")
    gsm_level = data.get("gsm_level")
    ltw_level = data.get("ltw_level")
    wvr_level = data.get("wvr_level")

    user = User.query.get(user_id)

    profile = Profile(user_id=user_id, world_id=world)
    profile.alc_level = alc_level if alc_level != None else 0
    profile.arm_level = arm_level if arm_level != None else 0
    profile.bsm_level = bsm_level if bsm_level != None else 0
    profile.crp_level = crp_level if crp_level != None else 0
    profile.cul_level = cul_level if cul_level != None else 0
    profile.gsm_level = gsm_level if gsm_level != None else 0
    profile.ltw_level = ltw_level if ltw_level != None else 0
    profile.wvr_level = wvr_level if wvr_level != None else 0
    # if this is the only profile, then set it to active
    profile.is_active = True if user.get_active_profile() == None else False
    db.session.add(profile)
    db.session.commit()

    return jsonify(one_profile_schema.dump(profile))


@bp.route("/get/all", methods=["GET"])
@fp.auth_required
def get_user_profiles():
    user_id = fp.current_user().id
    return jsonify(multi_profile_schema.dump(User.query.get(user_id).profiles))


@bp.route("/get/active", methods=["GET"])
@fp.auth_required
def get_active_profile():
    profile = fp.current_user().get_active_profile()
    return jsonify(one_profile_schema.dump(profile))


@bp.route("/get/<id>", methods=["GET"])
def get_profile_by_id(id):
    return jsonify(one_profile_schema.dump(Profile.query.get(id)))


@bp.route("/update/<id>", methods=["PUT"])
@fp.auth_required
def modify_profile_by_id(id):
    # add a check to ensure that the profile ID in question belongs to the logged-in user
    data = request.get_json()
    # check if the current_user also has a profile on this world, if so reject
    profile = Profile.query.get(id)
    if profile == None:
        return jsonify("No profile found")
    # check each job level, if any are not included then set them to 0 and add them to profile
    alc_level = data.get("alc_level")
    arm_level = data.get("arm_level")
    bsm_level = data.get("bsm_level")
    crp_level = data.get("crp_level")
    cul_level = data.get("cul_level")
    gsm_level = data.get("gsm_level")
    ltw_level = data.get("ltw_level")
    wvr_level = data.get("wvr_level")
    retainers = data.get("retainers")

    profile.alc_level = alc_level if alc_level != None else profile.alc_level
    profile.arm_level = arm_level if arm_level != None else profile.arm_level
    profile.bsm_level = bsm_level if bsm_level != None else profile.bsm_level
    profile.crp_level = crp_level if crp_level != None else profile.crp_level
    profile.cul_level = cul_level if cul_level != None else profile.cul_level
    profile.gsm_level = gsm_level if gsm_level != None else profile.gsm_level
    profile.ltw_level = ltw_level if ltw_level != None else profile.ltw_level
    profile.wvr_level = wvr_level if wvr_level != None else profile.wvr_level
    db.session.commit()

    if retainers != None and retainers != []:
        for retainer in retainers:
            process_retainer(profile, retainer)

    return jsonify(one_profile_schema.dump(profile))


# @bp.route("/retainers/add", methods=["POST"])
# @fp.auth_required
# def add_retainer_to_profile():
#     data = request.get_json()
#     name = data.get("name")
#     if name == None:
#         return jsonify("Error: No retainer name specified")
#     profile = fp.current_user().get_active_profile()
#     new_retainer = Retainer(profile_id=profile.id, name=name)
#     db.session.add(new_retainer)
#     db.session.commit()


def process_retainer(profile, retainer):
    print(retainer)
    if retainer["id"] == 0:
        new_retainer = Retainer(profile_id=profile.id, name=retainer["name"])
        db.session.add(new_retainer)
        db.session.commit()
    else:
        retainer_record = Retainer.query.get(retainer["id"])
        if retainer_record == None:
            print("No retainer record found")
        else:
            retainer_record.name = retainer["name"]
            db.session.commit()

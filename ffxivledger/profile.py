from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, current_user

from . import db
from .models import User, Profile, World, Retainer
from .schema import UserSchema, ProfileSchema

bp = Blueprint("profile", __name__, url_prefix="/profile")

one_profile_schema = ProfileSchema()
multi_profile_schema = ProfileSchema(many=True)


# GET endpoints


@bp.route("/get", methods=["GET"])
@jwt_required()
def get_user_profiles():
    return jsonify(multi_profile_schema.dump(current_user.profiles))


@bp.route("/get/active", methods=["GET"])
@jwt_required()
def get_active_profile():
    user = User.query.filter_by(username=get_jwt_identity()).first()
    profile = user.get_active_profile()
    return jsonify(one_profile_schema.dump(profile))


@bp.route("/get/<id>", methods=["GET"])
@jwt_required()
def get_profile_by_id(id):
    # an admin can get any profile but a user can only get their own
    # first, check to see if the requested profile belongs to the current user
    profile = Profile.query.get(id)
    if profile.user_id != current_user.id:
        # if not, check if the current user is an admin
        if current_user.roles != "admin":
            # if not, return 401
            return jsonify("Error: Not authorized"), 401
    return jsonify(one_profile_schema.dump(profile))


# POST endpoints


@bp.route("/add", methods=["POST"])
@jwt_required()
def add_profile():
    data = request.get_json()
    world = data.get("world")
    if world == None:
        return jsonify("Must include a world")

    query = Profile.query.filter_by(user_id=current_user.id, world_id=world).first()
    if query != None:
        return jsonify(f"Profile already exists on world {world}")

    # check each job level, if any are not included then set them to 0 and add them to profile
    alc_level = data.get("alcLevel")
    arm_level = data.get("armLevel")
    bsm_level = data.get("bsmLevel")
    crp_level = data.get("crpLevel")
    cul_level = data.get("culLevel")
    gsm_level = data.get("gsmLevel")
    ltw_level = data.get("ltwLevel")
    wvr_level = data.get("wvrLevel")
    retainers = data.get("retainers")

    profile = Profile(user_id=current_user.id, world_id=world)
    profile.alc_level = alc_level if alc_level != None else 0
    profile.arm_level = arm_level if arm_level != None else 0
    profile.bsm_level = bsm_level if bsm_level != None else 0
    profile.crp_level = crp_level if crp_level != None else 0
    profile.cul_level = cul_level if cul_level != None else 0
    profile.gsm_level = gsm_level if gsm_level != None else 0
    profile.ltw_level = ltw_level if ltw_level != None else 0
    profile.wvr_level = wvr_level if wvr_level != None else 0
    if retainers != None and retainers != []:
        process_retainers(profile, retainers)
    # if this is the only profile, then set it to active
    profile.is_active = True if current_user.get_active_profile() == None else False
    db.session.add(profile)
    db.session.commit()

    return jsonify(one_profile_schema.dump(profile))


# PUT endpoints


@bp.route("/update", methods=["PUT"])
@jwt_required()
def modify_profile_by_id():
    # add a check to ensure that the profile ID in question belongs to the logged-in user
    data = request.get_json()
    # check if the current_user also has a profile on this world, if so reject
    id = data.get("id")
    profile = Profile.query.get(id)
    if profile == None:
        return jsonify("No profile found")
    # check each job level, if any are not included then set them to 0 and add them to profile
    alc_level = data.get("alcLevel")
    arm_level = data.get("armLevel")
    bsm_level = data.get("bsmLevel")
    crp_level = data.get("crpLevel")
    cul_level = data.get("culLevel")
    gsm_level = data.get("gsmLevel")
    ltw_level = data.get("ltwLevel")
    wvr_level = data.get("wvrLevel")
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
        process_retainers(profile, retainers)

    return jsonify(one_profile_schema.dump(profile))


@bp.route("/activate", methods=["PUT"])
@jwt_required()
def set_active_profile():
    id = request.get_json().get("id")
    # first, ensure that the profile in question is owned by the sender of the request
    target_profile = Profile.query.get(id)
    if target_profile.user_id != current_user.id:
        return jsonify("Error: Not authorized"), 401
    # then, find all other profiles of that person and make sure they're set to inactive
    profile_list = Profile.query.filter_by(user_id=current_user.id).all()
    for profile in profile_list:
        profile.is_active = False
        db.session.commit()
    # finally, set the target profile to active
    target_profile.is_active = True
    db.session.commit()
    # return the active profile
    return jsonify(one_profile_schema.dump(target_profile))


# DELETE endpoints


@bp.route("/delete/<id>", methods=["DELETE"])
@jwt_required()
def delete_profile(id):
    # ensure that an admin can delete any profile, but a user can only delete their own
    # first, check if the user sending the request is the owner of the profile
    profile = Profile.query.get(id)
    if profile.user_id != current_user.id:
        # if not, check if they are admin
        if current_user.roles != "admin":
            return jsonify("Error: Not authorized"), 401
    # first, clear out the stuff that might get left behind.
    # I *think* that retainers will be orphaned and thus should get deleted automatically
    for skip in profile.skips:
        db.session.delete(skip)
        db.session.commit()
    for stock in profile.stock_list:
        db.session.delete(stock)
        db.session.commit()

    db.session.delete(profile)
    db.session.commit()
    return jsonify("Profile deleted"), 200


# utils


def process_retainers(profile, retainers):
    # first, query the db to get the retainers associated with the profile
    # (this needs to be a list comprehension to keep it from being updated as I change the db, I think)
    query = [x for x in Retainer.query.filter_by(profile_id=profile.id).all()]
    # then, 2 list comprehensions:
    # 1 for retainers in the query but not in the list (delete these)
    delete_list = [x for x in query if x.name not in retainers]
    for retainer in delete_list:
        db.session.delete(retainer)
        db.session.commit()
    # 1 filtering for retainers in the passed list but not in the query (add these)
    add_list = [x for x in retainers if x not in [y.name for y in query]]
    for retainer in add_list:
        new_retainer = Retainer(profile_id=profile.id, name=retainer)
        db.session.add(new_retainer)
        db.session.commit()

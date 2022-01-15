from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    set_access_cookies,
    get_jwt,
    unset_jwt_cookies,
    jwt_required,
    current_user,
)

from ffxivledger.utils import admin_required

from .models import User
from .schema import UserSchema
from . import db, jwt

bp = Blueprint("auth", __name__, url_prefix="/auth")
one_user_schema = UserSchema()
multi_user_schema = UserSchema(many=True)


# GET endpoints


@bp.route("/get", methods=["GET"])
@jwt_required()
@admin_required
def get_all_users():
    return jsonify(multi_user_schema.dump(User.query.all()))


@bp.route("/check", methods=["GET"])
@jwt_required(optional=True)
def check_for_logged_in_user():
    if current_user != None:
        return jsonify(one_user_schema.dump(current_user))
    return jsonify({})


@bp.route("/username/<username>", methods=["GET"])
def is_username_available(username):
    user = User.query.filter_by(username=username).first()
    if user != None:
        return jsonify(False)
    return jsonify(True)


# POST endpoints


@bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if User.query.filter_by(username=username).first() == None:
        new_user = User(username=username, password=User.hash_password(password))
        db.session.add(new_user)
        db.session.commit()
        response = jsonify(one_user_schema.dump(new_user))
        access_token = create_access_token(identity=username)
        set_access_cookies(response, access_token)
        return response
    return jsonify("User already exists"), 401


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user_query = User.query.filter_by(username=username).first()
    if user_query == None:
        return jsonify("Invalid username/password"), 401
    if not user_query.check_password(password):
        return jsonify("Invalid username/password"), 401
    response = jsonify(one_user_schema.dump(user_query))
    access_token = create_access_token(identity=username)
    set_access_cookies(response, access_token)
    return response


@bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response, 200


# PUT endpoints


@bp.route("/update", methods=["PUT"])
@jwt_required()
def update_user():
    # first, check if the current user is the one to be edited
    # if not, check for admin status
    # if not admin, reject

    data = request.get_json()
    id = data.get("id")

    if current_user.id != id:
        if current_user.roles != "admin":
            return jsonify("Error: Not authorized"), 401
    username = data.get("username")
    role = data.get("role")
    user = User.query.get(id)
    if user != None:
        user.username = username if username != None else user.username
        user.roles = role if role != None else user.roles
        db.session.commit()
    return jsonify(one_user_schema.dump(user))


# DELETE endpoints


@bp.route("/delete/<id>", methods=["DELETE"])
@jwt_required()
@admin_required
def admin_delete_user(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(multi_user_schema.dump(User.query.all()))


@bp.route("/delete", methods=["DELETE"])
@jwt_required()
def user_delete_self():
    response = jsonify("User deleted successfully")
    unset_jwt_cookies(response)
    db.session.delete(current_user)
    db.session.commit()
    return response


# utils


@current_app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(username=identity).first()

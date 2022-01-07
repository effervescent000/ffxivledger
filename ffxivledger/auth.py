from flask import Blueprint, request, jsonify

from .models import User
from .schema import UserSchema

# from .forms import SignUpForm, LoginForm, ManageUserForm
from . import db, guard

bp = Blueprint("auth", __name__, url_prefix="/auth")
one_user_schema = UserSchema()
multi_user_schema = UserSchema(many=True)


@bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json().get("user")
    username = data.get("username")
    password = data.get("password")
    if User.query.filter_by(username=username).first() == None:
        new_user = User(username=username, password=guard.hash_password(password))
        db.session.add(new_user)
        db.session.commit()
        user = guard.authenticate(username, password)
        return jsonify({"access_token": guard.encode_jwt_token(user)}, 200)
    else:
        return jsonify("User already exists")


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json().get("user")
    username = data.get("username")
    password = data.get("password")
    user = guard.authenticate(username, password)
    return jsonify({"access_token": guard.encode_jwt_token(user)}, 200)


@bp.route("/refresh", methods=["POST"])
def refresh_token():
    data = request.get_json().get("loggedInUser")
    return guard.refresh_jwt_token(data)


@bp.route("/get/all", methods=["GET"])
def get_all_users():
    return jsonify(multi_user_schema.dump(User.query.all()))


@bp.route("/update", methods=['PUT'])
def update_user():
    data = request.get_json()
    username = data.get("username")
    role = data.get("role")
    # right now I can only update roles
    user = User.query.filter_by(username=username).first()
    if user != None:
        user.roles = role
        db.session.commit()
    return jsonify(one_user_schema.dump(user))


# @login_manager.user_loader
# def load_user(user_id):
#     if user_id is not None:
#         return User.query.get(user_id)
#     return None


# @login_manager.unauthorized_handler
# def unauthorized():
#     flash("You must be logged in to view that page")
#     return redirect(url_for("auth.login"))

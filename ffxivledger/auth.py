from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import login_required, logout_user, current_user, login_user

from .utils import admin_required

from .models import User
from .forms import SignUpForm, LoginForm, ManageUserForm
from . import db, login_manager

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/signup', methods=('GET', 'POST'))
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user is None:
            user = User()
            user.username = form.username.data
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard.index'))
        flash('A user with that name already exists')
    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(password=form.password.data):
            login_user(user)
            # TODO look into how to secure the next_page thing
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        flash('Invalid username/password combination')
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('dashboard.index'))


@bp.route('/manage')
@login_required
def user_management():
    user_list = User.query.all()
    return render_template('auth/account_management.html', users=user_list)


@bp.route('manage/<id>', methods=('POST', 'GET'))
@login_required
@admin_required
def admin_manage_user(id):
    form = ManageUserForm()
    user = User.query.get(id)
    if form.validate_on_submit():
        user.username = form.username.data
        if form.role.data == '':
            user.role = None
        else:
            user.role = form.role.data
        db.session.commit()
        return redirect(url_for('auth.user_management'))
    return render_template('auth/edit_user.html', form=form, user=user)


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page')
    return redirect(url_for('auth.login'))

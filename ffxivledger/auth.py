from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import login_required, logout_user, current_user, login_user

from .models import User
from .forms import SignUpForm, LoginForm
from . import db, login_manager

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    # redirect if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user and user.check_password(password=form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        flash('Invalid username/password combination')
        return redirect(url_for('auth.login'))
    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=('GET', 'POST'))
def register():
    form = SignUpForm()
    if form.validate_on_submit():
        print('Got through validation')
        existing_user = User.query.filter_by(name=form.name.data).first()
        if existing_user is None:
            user = User()
            user.name = form.name.data
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            print('Success!')
            return redirect(url_for('dashboard.index'))
        flash('A user with that name already exists')
    return render_template('auth/register.html', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('dashboard.index'))


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page')
    return redirect(url_for('auth.login'))

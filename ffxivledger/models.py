from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db

name_length = 200
time_format = '%Y-%m-%d %H:%M'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    stock_list = db.relationship('Stock', backref='user', lazy=True, cascade="all, delete-orphan")
    # valid roles are admin and super_user
    role = db.Column(db.String(50))
    profiles = db.relationship('Profile', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        """Create hashed password"""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    world = db.Column(db.String(50), nullable=False)
    alc_level = db.Column(db.Integer)
    arm_level = db.Column(db.Integer)
    bsm_level = db.Column(db.Integer)
    crp_level = db.Column(db.Integer)
    cul_level = db.Column(db.Integer)
    gsm_level = db.Column(db.Integer)
    ltw_level = db.Column(db.Integer)
    wvr_level = db.Column(db.Integer)


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    # value is the stripped down form of the name, i.e. "patrician's bottoms" -> "patricians_bottoms"
    # value = db.Column(db.String(name_length), primary_key=True)
    name = db.Column(db.String(name_length), unique=True, nullable=False)
    # valid types are: 'product', 'intermediate', 'material'
    # type = db.Column(db.String(50), nullable=False)
    transactions = db.relationship('Transaction', backref='item', lazy=True, cascade="all, delete-orphan")
    stock = db.relationship('Stock', backref='item', lazy=True, cascade="all, delete-orphan")

    components = db.relationship('Component', backref='item', lazy=True, cascade='all, delete-orphan')
    recipes = db.relationship('Recipe', backref="item", lazy=True, cascade='all, delete-orphan')
    # products = db.relationship('Product', backref='item', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return '<Item {}>'.format(self.name)


    def process_transaction(self, gil_value, time, amount, user_id):
        transaction = Transaction(
            gil_value=gil_value,
            time=time,
            amount=amount,
            item_id=self.id,
            user_id=user_id
        )
        db.session.add(transaction)
        db.session.commit()
        # now adjust the amount stored in the stock table
        self._adjust_stock(amount, user_id)
        return transaction


    def _adjust_stock(self, num, user_id, overwrite=False):
        """Adjust the amount of a product in stock. If override is True, then overwrite the current stock value.
        If False, then +/- it"""
        num = int(num)
        stock_row = Stock.query.filter_by(item_id=self.id,user_id=user_id).one_or_none()
        if stock_row is None:
            # always overwrite if creating a new row
            stock_row = Stock(amount=num, item_id=self.id, user_id=user_id)
            db.session.add(stock_row)
        elif overwrite is True:
            stock_row.amount = num
        else:
            stock_row.amount += num
        # ensure the amount doesn't go below 0
        if stock_row.amount < 0:
            stock_row.amount = 0
        db.session.commit()

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gil_value = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(50), nullable=False)
    # the amount purchased/sold at this value
    amount = db.Column(db.Integer, nullable=False, default=1)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Transaction #{}>'.format(self.id)


class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # keep track of the amount currently in stock
    amount = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.String(3), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    item_quantity = db.Column(db.Integer, nullable=False)
    components = db.relationship('Component', backref='recipe', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Recipe {} for {}>'.format(int(self.id), self.item_id)


class Component(db.Model):
    __tablename__ = 'components'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    item_quantity = db.Column(db.Integer, nullable=False, default=1)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))

    def __repr__(self):
        return f"Recipe {self.id} for recipe {self.recipe_id}"


# class Product(db.Model):
#     __tablename__ = 'products'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     item_value = db.Column(db.String(name_length), db.ForeignKey('items.value'))
#     item_quantity = db.Column(db.Integer, nullable=False, default=1)
#     recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))

#     def __repr__(self):
#         return '<Product {} of recipe {}>'.format(self.item_value, int(self.recipe_id))

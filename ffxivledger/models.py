from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db

name_length = 200


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    stock_list = db.relationship('Stock', backref='user', lazy=True)

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def set_password(self, password):
        """Create hashed password"""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Item(db.Model):
    __tablename__ = 'items'
    # value is the stripped down form of the name, i.e. "patrician's bottoms" -> "patricians_bottoms"
    value = db.Column(db.String(name_length), primary_key=True)
    name = db.Column(db.String(name_length), unique=True, nullable=False)
    # valid types are: 'product', 'intermediate', 'material'
    type = db.Column(db.String(50), nullable=False)
    prices = db.relationship('Price', backref='item', lazy=True)
    stock = db.relationship('Stock', backref='item', lazy=True)

    components = db.relationship('Component', backref='item', lazy=True)
    products = db.relationship('Product', backref='item', lazy=True)

    def __repr__(self):
        return '<Item {}>'.format(self.name)

    def adjust_stock(self, num, overwrite=False):
        """Adjust the amount of a product in stock. If override is True, then overwrite the current stock value.
        If False, then +/- it"""
        # TODO make this account for multiple users in like... any way
        stock_row = Stock.query.filter(Stock.item_value == self.value).one_or_none()
        if stock_row is None:
            # always overwrite if creating a new row
            stock_row = Stock(amount=num, item_value=self.value)
            db.session.add(stock_row)
        elif overwrite is True:
            stock_row.amount = num
        else:
            stock_row.amount += num
        # ensure the amount doesn't go below 0
        if stock_row.amount < 0:
            stock_row.amount = 0
        db.session.commit()


class Price(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    price_input = db.Column(db.Integer, nullable=False)
    price_time = db.Column(db.DateTime, nullable=False)
    # the amount purchased/sold at this price
    amount = db.Column(db.Integer, nullable=False, default=1)
    item_value = db.Column(db.String(name_length),
                           db.ForeignKey('items.value'))

    def __repr__(self):
        return '<Price {}>'.format(str(self.price_input))


class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # keep track of the amount currently in stock
    amount = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_value = db.Column(db.String(200), db.ForeignKey('items.value'))


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job = db.Column(db.String(3), nullable=False)
    components = db.relationship('Component', backref='recipe')
    product = db.relationship('Product', backref='recipe')


class Component(db.Model):
    __tablename__ = 'components'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_value = db.Column(db.String(name_length), db.ForeignKey('items.value'))
    item_quantity = db.Column(db.Integer, nullable=False, default=1)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_value = db.Column(db.String(name_length), db.ForeignKey('items.value'))
    item_quantity = db.Column(db.Integer, nullable=False, default=1)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))

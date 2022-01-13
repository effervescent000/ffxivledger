from . import db
from passlib.hash import pbkdf2_sha256 as hash

name_length = 200
time_format = "%Y-%m-%d %H:%M"


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    roles = db.Column(db.String(200))
    profiles = db.relationship("Profile", backref="user", lazy=True, cascade="all, delete-orphan")
    # profile_list = db.relationship("ProfileList", backref="user", lazy=True, uselist=False, cascade="all, delete-orphan")
    is_active = db.Column(db.Boolean, default=True, server_default="true")

    def __repr__(self):
        return "<User {}>".format(self.username)

    @staticmethod
    def hash_password(password):
        return hash.hash(password)

    def check_password(self, input):
        return hash.verify(input, self.password)

    def get_active_profile(self):
        for x in self.profiles:
            if x.is_active:
                return x

class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_active = db.Column(db.Boolean, nullable=False)
    world_id = db.Column(db.Integer, db.ForeignKey("worlds.id"))
    alc_level = db.Column(db.Integer)
    arm_level = db.Column(db.Integer)
    bsm_level = db.Column(db.Integer)
    crp_level = db.Column(db.Integer)
    cul_level = db.Column(db.Integer)
    gsm_level = db.Column(db.Integer)
    ltw_level = db.Column(db.Integer)
    wvr_level = db.Column(db.Integer)

    stock_list = db.relationship("Stock", backref="profile", lazy=True, cascade="all, delete-orphan")
    skips = db.relationship("Skip", backref="profile", lazy=True, cascade="all, delete-orphan")
    retainers = db.relationship("Retainer", backref="profile", lazy=True, cascade="all, delete-orphan")


class Retainer(db.Model):
    __tablename__ = "retainers"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"))
    name = db.Column(db.String(20), nullable=False)


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    # value is the stripped down form of the name, i.e. "patrician's bottoms" -> "patricians_bottoms"
    # value = db.Column(db.String(name_length), primary_key=True)
    name = db.Column(db.String(name_length), unique=True, nullable=False)
    # valid types are: 'product', 'intermediate', 'material'
    # type = db.Column(db.String(50), nullable=False)
    transactions = db.relationship("Transaction", backref="item", lazy=True, cascade="all, delete-orphan")
    stock = db.relationship("Stock", backref="item", lazy=True, cascade="all, delete-orphan")

    components = db.relationship("Component", backref="item", lazy=True, cascade="all, delete-orphan")
    recipes = db.relationship("Recipe", backref="item", lazy=True, cascade="all, delete-orphan")

    skips = db.relationship("Skip", backref="item", lazy=True, cascade="all, delete-orphan")
    item_stats = db.relationship("ItemStats", backref="item", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return "<Item {}>".format(self.name)

    def process_transaction(self, gil_value, time, amount, profile_id):
        transaction = Transaction(gil_value=gil_value, time=time, amount=amount, item_id=self.id, profile_id=profile_id)
        db.session.add(transaction)
        db.session.commit()
        # now adjust the amount stored in the stock table
        self._adjust_stock(amount, profile_id)
        return transaction

    def _adjust_stock(self, num, profile_id, overwrite=False):
        """Adjust the amount of a product in stock. If override is True, then overwrite the current stock value.
        If False, then +/- it"""
        num = int(num)
        stock_row = Stock.query.filter_by(item_id=self.id, profile_id=profile_id).first()
        if stock_row is None:
            # always overwrite if creating a new row
            stock_row = Stock(amount=num, item_id=self.id, profile_id=profile_id)
            db.session.add(stock_row)
        elif overwrite is True:
            stock_row.amount = num
        else:
            stock_row.amount += num
        # ensure the amount doesn't go below 0
        if stock_row.amount < 0:
            stock_row.amount = 0
        db.session.commit()


class Skip(db.Model):
    __tablename__ = "skips"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    time = db.Column(db.String(200))


class ItemStats(db.Model):
    __tablename__ = "stats"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    world_id = db.Column(db.Integer, db.ForeignKey("worlds.id"))

    stats_updated = db.Column(db.String(200))
    craft_cost = db.Column(db.Float)
    price = db.Column(db.Float)
    sales_velocity = db.Column(db.Float)

    def __repr__(self):
        return f"<ItemStats {self.item.name} on {self.world.name}>"


class World(db.Model):
    __tablename__ = "worlds"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    datacenter_id = db.Column(db.Integer, db.ForeignKey("datacenters.id"))

    profiles = db.relationship("Profile", backref="world", lazy=True, cascade="all, delete-orphan")
    itemstats = db.relationship("ItemStats", backref="world", lazy=True, cascade="all, delete-orphan")


class Datacenter(db.Model):
    __tablename__ = "datacenters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    worlds = db.relationship("World", backref="datacenter", lazy=True, cascade="all, delete-orphan")


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gil_value = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(50), nullable=False)
    # the amount purchased/sold at this value
    amount = db.Column(db.Integer, nullable=False, default=1)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"))

    def __repr__(self):
        return "<Transaction #{}>".format(self.id)


class Stock(db.Model):
    __tablename__ = "stock"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # keep track of the amount currently in stock
    amount = db.Column(db.Integer, nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"))
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))


class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.String(3), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    item_quantity = db.Column(db.Integer, nullable=False)
    components = db.relationship("Component", backref="recipe", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return "<Recipe {} for {}>".format(int(self.id), self.item_id)


class Component(db.Model):
    __tablename__ = "components"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    item_quantity = db.Column(db.Integer, nullable=False, default=1)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"))

    def __repr__(self):
        return f"<Component {self.id} for recipe {self.recipe_id}>"

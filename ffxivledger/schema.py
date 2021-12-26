from ffxivledger.models import World
from . import ma


class WorldSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "datacenter_id")

one_world_schema = WorldSchema()
multi_worlds_schema = WorldSchema(many=True)


class ProfileSchema(ma.Schema):
    class Meta:
        fields = (
            "id",
            "user_id",
            "world",
            "alc_level",
            "arm_level",
            "bsm_level",
            "crp_level",
            "cul_level",
            "gsm_level",
            "ltw_level",
            "wvr_level",
        )
    world = ma.Nested(one_world_schema)


profiles_schema = ProfileSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "roles")


class ComponentSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_id", "item_quantity", "recipe_id")


components_schema = ComponentSchema(many=True)


class RecipeSchema(ma.Schema):
    class Meta:
        fields = ("id", "job", "level", "item_id", "components")

    components = ma.Nested(components_schema)


multi_recipe_schema = RecipeSchema(many=True)


class ItemSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "recipes")

    recipes = ma.Nested(multi_recipe_schema)


one_item_schema = ItemSchema()


class TransactionSchema(ma.Schema):
    class Meta:
        fields = ("id", "gil_value", "time", "amount", "item_id")


class StockSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_id", "amount", "item")

    item = ma.Nested(one_item_schema)


class DatacenterSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "worlds")

    worlds = ma.Nested(multi_worlds_schema)

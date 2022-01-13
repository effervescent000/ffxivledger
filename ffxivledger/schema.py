from . import ma


class WorldSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "datacenter_id")

one_world_schema = WorldSchema()
multi_worlds_schema = WorldSchema(many=True)


class RetainerSchema(ma.Schema):
    class Meta:
        fields = ("id", "profile_id", "name")


multi_retainer_schema = RetainerSchema(many=True)


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
            "retainers",
            "is_active"
        )
    world = ma.Nested(one_world_schema)
    retainers = ma.Nested(multi_retainer_schema)


multi_profiles_schema = ProfileSchema(many=True)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "roles", "profiles")
    profiles = ma.Nested(multi_profiles_schema)


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


class ItemStatsSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_id", "world_id", "item", "stats_updated", "craft_cost", "price", "sales_velocity")
    item = ma.Nested(one_item_schema)


class SkipSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_id", "profile_id", "time")


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

from . import ma


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "role")


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


class ItemSchema(ma.Schema):
    class Meta:
        fields = ("id", "name")


class TransactionSchema(ma.Schema):
    class Meta:
        fields = ("id", "gil_value", "time", "amount", "item_value")


class StockSchema(ma.Schema):
    class Meta:
        fields = ("item_id", "amount")


class RecipeSchema(ma.Schema):
    class Meta:
        fields = ("id", "job", "level")


class ComponentSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_value", "item_quantity", "recipe_id")


# class ProductSchema(ma.Schema):
#     class Meta:
#         fields = ("id", "item_value", "item_quantity", "recipe_id")

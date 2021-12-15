from . import ma


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


class ProductSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_value", "item_quantity", "recipe_id")

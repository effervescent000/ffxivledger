from . import ma


class ItemSchema(ma.Schema):
    class Meta:
        fields = ("value", "name", "type")


class TransactionSchema(ma.Schema):
    class Meta:
        fields = ("id", "gil_value", "time", "amount", "item_value")


class StockSchema(ma.Schema):
    class Meta:
        fields = ("item_value", "amount")


class RecipeSchema(ma.Schema):
    class Meta:
        fields = ("id", "job")


class ComponentSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_value", "item_quantity", "recipe_id")


class ProductSchema(ma.Schema):
    class Meta:
        fields = ("id", "item_value", "item_quantity", "recipe_id")

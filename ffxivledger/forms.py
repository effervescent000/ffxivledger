from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, Form, FormField, StringField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms.fields.core import FieldList

from .utils import get_item_options, get_craftables_options
from .models import name_length


class DashboardForm(FlaskForm):
    item = SelectField(choices=get_item_options())
    amount = IntegerField()
    price = IntegerField()
    sale_button = SubmitField(u'Add sale')
    purchase_button = SubmitField(u'Add purchase')
    view_button = SubmitField(u'View data')
    # buttons to change stock amounts w/o adding price data
    add_stock_button = SubmitField(u'Add stock')
    remove_stock_button = SubmitField(u'Remove stock')
    # TODO eventually move recipe-management to its own page, rather than dumping it on the dashboard
    create_recipe_button = SubmitField(u'Create recipe')
    view_recipes_button = SubmitField(u'View recipe(s)')

    # def validate_sale_button(self, field):
    #     if self.sale_button.data:
    #         if self.amount.data is None:
    #             raise ValidationError('Sale amount required')
    #         if self.price.data is None:
    #             raise ValidationError('Sale price required')


class CreateItemForm(FlaskForm):
    item_type_choices = [
        ('product', 'Product'),
        ('intermediate', 'Intermediate item'),
        ('material', 'Raw material')
    ]

    item_name = StringField(u'Item name', validators=[InputRequired(), Length(max=name_length)])
    item_type = SelectField(u'Item type', choices=item_type_choices)
    save_button = SubmitField(u'Save')


# recipe related forms
class RecipeLineForm(Form):
    item_options = get_item_options()

    item_value = SelectField(choices=item_options)
    item_quantity = IntegerField()


class CreateRecipeForm(FlaskForm):
    product_name = SelectField(choices=get_craftables_options())
    product_quantity = IntegerField(default=1)
    job_field = SelectField(choices=['ALC', 'GSM', 'WVR'])
    line_item_list = FieldList(FormField(RecipeLineForm), min_entries=6)
    save_button = SubmitField()

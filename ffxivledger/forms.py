from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, Form, FormField, StringField, SubmitField, PasswordField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from wtforms.fields import FieldList
from flask_login import current_user

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


class PriceForm(FlaskForm):
    item_value = SelectField(choices=get_item_options())
    price_input = IntegerField('Price point', validators=[InputRequired()])
    item_quantity = IntegerField()
    price_time = StringField('Transaction time')

    save_button = SubmitField()


# recipe related forms
class RecipeLineForm(Form):
    item_value = SelectField(choices=get_item_options())
    item_quantity = IntegerField()


class CreateRecipeForm(FlaskForm):
    product_name = SelectField(choices=get_craftables_options())
    product_quantity = IntegerField(default=1)
    job_field = SelectField(choices=['ALC', 'GSM', 'WVR'])
    line_item_list = FieldList(FormField(RecipeLineForm), min_entries=6)
    save_button = SubmitField()


# user/login-related forms
class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    # email = StringField('Email', [InputRequired(), Email(message='Enter a valid email')])
    password = PasswordField('Password',
                             validators=[Length(min=6, message='Choose a longer password'), InputRequired()])
    confirm_password = PasswordField('Confirm password',
                                     validators=[InputRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')


class ManageUserForm(FlaskForm):
    # TODO figure out how to prepopulate defaults here based on current user
    username = StringField('Username')
    role = SelectField('Role', choices=[('', '---'), ('super_user', 'SuperUser'), ('admin', 'Admin')])
    submit = SubmitField('Save')
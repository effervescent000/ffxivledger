# from flask import Flask
# from flask_wtf import FlaskForm
# from wtforms import (
#     IntegerField, SelectField, Form, FormField, StringField, SubmitField, PasswordField, ValidationError, TextAreaField
# )
# from wtforms.validators import InputRequired, Length, Email, EqualTo
# from wtforms.fields import FieldList
# from flask_login import current_user

# from .utils import get_item_options, get_craftables_options
# from .models import name_length


# class DashboardForm(FlaskForm):
#     item = SelectField(choices=get_item_options())
#     amount = IntegerField('Amount')
#     gil_value = IntegerField('Gil')
#     sale_button = SubmitField(u'Add sale')
#     purchase_button = SubmitField(u'Add purchase')
#     view_button = SubmitField(u'View data')
    
#     add_stock_button = SubmitField(u'Add stock')
#     remove_stock_button = SubmitField(u'Remove stock')
#     # TODO eventually move recipe-management to its own page, rather than dumping it on the dashboard
#     create_recipe_button = SubmitField(u'Create recipe')
#     view_recipes_button = SubmitField(u'View recipe(s)')

#     def validate(self):
#         if self.sale_button.data:
#             if self.amount.data is None:
#                 raise ValidationError('Sale amount required')
#             if self.gil_value.data is None:
#                 raise ValidationError('Sale value required')
#         if self.remove_stock_button.data:
#             if self.amount.data is None:
#                 raise ValidationError('Amount required')
#         if self.purchase_button.data:
#             if self.gil_value.data is None:
#                 raise ValidationError('Purchase value required')
#             if self.amount.data is None:
#                 raise ValidationError('Amount required')
#         if self.add_stock_button.data:
#             if self.amount.data is None:
#                 raise ValidationError('Amount required')
#         return True


# class CreateItemForm(FlaskForm):
#     item_type_choices = [
#         ('product', 'Product'),
#         ('intermediate', 'Intermediate item'),
#         ('material', 'Raw material')
#     ]
    
#     item_name = StringField(u'Item name', validators=[InputRequired(), Length(max=name_length)])
#     item_type = SelectField(u'Item type', choices=item_type_choices)
#     save_button = SubmitField(u'Save')


# class TransactionForm(FlaskForm):
#     item_value = SelectField(choices=get_item_options())
#     gil_value = IntegerField('Gil value', validators=[InputRequired()])
#     item_quantity = IntegerField()
#     time = StringField('Transaction time')

#     save_button = SubmitField()


# class CraftingQueueForm(FlaskForm):
#     queue_dropdown = SelectField('Number to queue', choices=[3,5,10])
#     queue_button = SubmitField('Queue')
#     queue_text = TextAreaField(render_kw={'readonly': True})


# class CraftingOutputForm(FlaskForm):
#     output_text= TextAreaField(render_kw={'readonly': True})
#     clear_button = SubmitField('Clear log')

# # recipe related forms
# class RecipeLineForm(Form):
#     item_value = SelectField(choices=get_item_options())
#     item_quantity = IntegerField()


# class CreateRecipeForm(FlaskForm):
#     product_name = SelectField(choices=get_craftables_options())
#     product_quantity = IntegerField(default=1)
#     job_field = SelectField(choices=['ALC', 'ARM', 'BSM', 'CRP', 'GSM','LTW', 'WVR'])
#     line_item_list = FieldList(FormField(RecipeLineForm), min_entries=6)
#     save_button = SubmitField()


# # user/login-related forms
# class SignUpForm(FlaskForm):
#     username = StringField('Username', validators=[InputRequired()])
#     # email = StringField('Email', [InputRequired(), Email(message='Enter a valid email')])
#     password = PasswordField('Password', validators=[
#         Length(min=6, message='Choose a longer password'), 
#         InputRequired()
#         ])
#     confirm_password = PasswordField('Confirm password', validators=[
#         InputRequired(), 
#         EqualTo('password', message='Passwords must match.')
#         ])
#     submit = SubmitField('Register')


# class LoginForm(FlaskForm):
#     username = StringField('Username', validators=[InputRequired()])
#     password = PasswordField('Password', validators=[InputRequired()])
#     submit = SubmitField('Login')


# class ManageUserForm(FlaskForm):
#     username = StringField('Username', validators=[InputRequired(), Length(min=5, max=50)])
#     role = SelectField('Role', choices=[('', '---'), ('super_user', 'SuperUser'), ('admin', 'Admin')])
#     submit = SubmitField('Save')
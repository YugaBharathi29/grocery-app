from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    address = TextAreaField('Delivery Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    image = FileField('Upload Image', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Images only!')])
    image_url = StringField('Or Image URL', validators=[Optional()])
    is_active = BooleanField('Show to Customers', default=True)
    submit = SubmitField('Save Category')


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    price = FloatField('Price (₹)', validators=[DataRequired(), NumberRange(min=0, message='Price must be positive')])
    stock = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0, message='Stock cannot be negative')])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Images only!')])
    image_url = StringField('Or Image URL', validators=[Optional()])
    is_active = BooleanField('Show to Customers', default=True)
    submit = SubmitField('Save Product')


class CheckoutForm(FlaskForm):
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired()])
    submit = SubmitField('Place Order')


class UserManagementForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=15)])
    address = TextAreaField('Address', validators=[Optional()])
    is_active = BooleanField('Account Active', default=True)
    is_admin = BooleanField('Admin Privileges', default=False)
    submit = SubmitField('Update User')


class OrderStatusForm(FlaskForm):
    status = SelectField('Order Status', 
                        choices=[
                            ('Pending', 'Pending'),
                            ('Processing', 'Processing'),
                            ('Shipped', 'Shipped'),
                            ('Delivered', 'Delivered'),
                            ('Cancelled', 'Cancelled')
                        ],
                        validators=[DataRequired()])
    submit = SubmitField('Update Status')


class BulkUploadForm(FlaskForm):
    """Form for bulk uploading products via CSV/Excel file"""
    file = FileField('Upload CSV or Excel File', 
                     validators=[
                         FileRequired(message='Please select a file to upload'),
                         FileAllowed(['csv', 'xlsx', 'xls'], 'Only CSV and Excel files are allowed!')
                     ])
    submit = SubmitField('Upload Products')


# ========== NEW: PROFILE FORM ==========

class ProfileForm(FlaskForm):
    """Form for user profile management"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(min=10, max=15)])
    address = TextAreaField('Delivery Address', validators=[Optional()])
    
    # Password change fields (optional)
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                     validators=[Optional(), EqualTo('new_password', message='Passwords must match')])
    
    submit = SubmitField('Update Profile')

class SubscriptionForm(FlaskForm):
    """Form for creating/editing subscriptions"""
    name = StringField('Subscription Name', validators=[DataRequired(), Length(min=3, max=200)])
    frequency = SelectField('Delivery Frequency', 
                           choices=[
                               ('daily', 'Daily'),
                               ('weekly', 'Weekly')
                           ],
                           validators=[DataRequired()])
    delivery_time = SelectField('Preferred Delivery Time',
                               choices=[
                                   ('morning', 'Morning (6 AM - 12 PM)'),
                                   ('evening', 'Evening (4 PM - 8 PM)')
                               ],
                               validators=[DataRequired()])
    submit = SubmitField('Create Subscription')


class AddSubscriptionItemForm(FlaskForm):
    """Form for adding products to subscription"""
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add to Subscription')

from flask_wtf import FlaskForm
from wtforms import (BooleanField, StringField, HiddenField,
                     SelectField, SubmitField)
from wtforms.validators import DataRequired, Length


class PartForm(FlaskForm):
    """Form to add parts"""
    p_type = SelectField(
        'Type',
        choices=[('fw', 'Front Wheel'), ('rw', 'Rear Wheel'),
                 ('cn', 'chain'), ('ft', 'Front Tire'), ('rt', 'Rear Tire'),
                 ('bc', 'Brake Cables'), ('sc', 'Shifter Cables')],
        validate_choice=True
    )
    dt = StringField(
        'Date Added',
        [DataRequired()]
    )
    brand = StringField('Brand', [DataRequired()])
    price = StringField('Price')
    weight = StringField('Weight')
    size = StringField('Size')
    model = StringField('Model')
    virt = BooleanField('Virtual')
    bike_id = HiddenField('bike_id')
    retire = HiddenField('retired')
    retired_part = HiddenField('retired_part')
    submit = SubmitField("Add part")

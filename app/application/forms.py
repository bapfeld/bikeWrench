from flask_wtf import FlaskForm
from wtforms import (BooleanField, StringField, HiddenField,
                     SelectField, SubmitField, TextField)
from wtforms.validators import DataRequired, Length


class PartForm(FlaskForm):
    """Form to add parts"""
    p_type = SelectField(
        'Type',
        choices=[('Front Wheel', 'Front Wheel'), ('Rear Wheel', 'Rear Wheel'),
                 ('Chain', 'Chain'), ('Front Tire', 'Front Tire'), ('Rear Tire', 'Rear Tire'),
                 ('Brake Cables', 'Brake Cables'), ('Shifter Cables', 'Shifter Cables'),
                 ('Cassette', 'Cassette'), ('Front Brake Caliper', 'Front Brake Caliper')]
    )
    dt = StringField(
        'Date Added',
        [DataRequired()]
    )
    brand = StringField('Brand')
    price = StringField('Price')
    weight = StringField('Weight')
    size = StringField('Size')
    model = StringField('Model')
    virt = BooleanField('Virtual')
    submit = SubmitField("Add part")


class MaintenanceForm(FlaskForm):
    """Form to add maintenance"""
    work = TextField('Work performed', [DataRequired(),
                                        Length(min=5,
                                               message='Maintenance log too short')])
    dt = StringField('Date maintained', [DataRequired()])
    submit = SubmitField("Add maintenance log")


class BikeForm(FlaskForm):
    """Form to add a new bike"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'edit' in kwargs:
            self.submit.label.text = 'Edit bike'
        
    nm = StringField('Name', [DataRequired(), Length(min=3,
                                                     message='Longer name needed')])
    color = StringField('Color')
    purchase = StringField('Date purchased', [DataRequired()])
    mfg = StringField('Manufacturer')
    price = StringField('Price')
    submit = SubmitField('Add bike')


class DateLimitForm(FlaskForm):
    """Form to input start/end dates"""
    start_date = StringField('Start Date')
    end_date = StringField('End Date')
    submit = SubmitField('Refresh Details')


class RiderForm(FlaskForm):
    """Form for adding/editing a rider"""
    rider = StringField('Rider Name', [DataRequired()])
    units = SelectField(
        'Unit type preference',
        choices=[('imperial', 'Imperial'), ('metric', 'metric')]
    )
    submit = SubmitField('Update rider info')

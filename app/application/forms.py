from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    StringField,
    HiddenField,
    SelectField,
    SubmitField,
    StringField,
    FloatField,
)
from wtforms.validators import DataRequired, Length


class PartForm(FlaskForm):
    """Form to add parts"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "edit" in kwargs:
            self.submit.label.text = "Edit part"

    p_type = SelectField(
        "Type",
        choices=[
            ("Front Wheel", "Front Wheel"),
            ("Rear Wheel", "Rear Wheel"),
            ("Chain", "Chain"),
            ("Front Tire", "Front Tire"),
            ("Rear Tire", "Rear Tire"),
            ("Brake Cables", "Brake Cables"),
            ("Shifter Cables", "Shifter Cables"),
            ("Cassette", "Cassette"),
            ("Front Brake Caliper", "Front Brake Caliper"),
            ("Bar Tape", "Bar Tape"),
        ],
    )
    dt = StringField("Date Added", [DataRequired()])
    brand = StringField("Brand", [DataRequired(False)])
    price = FloatField("Price", [DataRequired(False)])
    weight = FloatField("Weight", [DataRequired(False)])
    size = StringField("Size", [DataRequired(False)])
    model = StringField("Model", [DataRequired(False)])
    virt = BooleanField("Virtual")
    submit = SubmitField("Add part")


class MaintenanceForm(FlaskForm):
    """Form to add maintenance"""

    work = StringField(
        "Work performed",
        [DataRequired(), Length(min=5, message="Maintenance log too short")],
    )
    dt = StringField("Date maintained", [DataRequired()])
    submit = SubmitField("Add maintenance log")


class BikeForm(FlaskForm):
    """Form to add a new bike"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "edit" in kwargs:
            self.submit.label.text = "Edit bike"
        # if 'bike_name' in kwargs:
        #     self.nm.default = kwargs['bike_name']

    nm = StringField(
        "Name", [DataRequired(), Length(min=3, message="Longer name needed")]
    )
    color = StringField("Color")
    purchase = StringField("Date purchased", [DataRequired()])
    mfg = StringField("Manufacturer")
    price = StringField("Price")
    submit = SubmitField("Add bike")


class DateLimitForm(FlaskForm):
    """Form to input start/end dates"""

    start_date = StringField("Start Date")
    end_date = StringField("End Date")
    submit = SubmitField("Refresh Details")


class RiderForm(FlaskForm):
    """Form for adding/editing a rider"""

    rider = StringField("Rider Name", [DataRequired()])
    units = SelectField(
        "Unit type preference", choices=[("imperial", "Imperial"), ("metric", "metric")]
    )
    submit = SubmitField("Update rider info")

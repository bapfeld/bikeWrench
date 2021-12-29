from . import db

class Riders(db.Model):
    """Data model for rider(s)"""
    __tablename__ = 'riders'

    name = db.Column(db.String,
                     primary_key=True
                     )
    units = db.Column(db.String,
                      index=False,
                      unique=False,
                      nullable=True)
    r_ktn = db.Column(db.String,
                      index=False,
                      unique=False,
                      nullable=True)
    tkn_exp = db.Column(db.DateTime,
                        index=False,
                        unique=False,
                        nullable=True)


class Bikes(db.Model):
    """Data model for bikes"""
    __tablename__ = 'bikes'

    bike_id = db.Column(db.Integer,
                        primary_key=True,
                        unique=True)
    name = db.Column(db.String,
                     index=False,
                     unique=True,
                     nullable=True)
    color = db.Column(db.String,
                     index=False,
                     unique=False,
                     nullable=True)
    purchased = db.Column(db.Date,
                          index=False,
                          unique=False,
                          nullable=True)
    price = db.Column(db.Float,
                      index=False,
                      unique=False,
                      nullable=True)
    mfg = db.Column(db.String,
                     index=False,
                     unique=False,
                     nullable=True)


class Rides(db.Model):
    """Data model for rides"""
    __tablename__ = 'rides'
    
    ride_id = db.Column(db.Integer,
                        primary_key=True,
                        unique=True)
    bike = db.Column(db.String,
                     index=False,
                     unique=False,
                     nullable=True,
                     foreign_key='bikes.bike_id')
    distance = db.Column(db.BigInteger,
                         index=False,
                         unique=False,
                         nullable=True)
    name = db.Column(db.String,
                     index=False,
                     unique=False,
                     nullable=True)
    date = db.Column(db.Date,
                     index=False,
                     unique=False,
                     nullable=True)
    moving_time = db.Column(db.BigInteger,
                            index=False,
                            unique=False,
                            nullable=True)
    elapsed_time = db.Column(db.BigInteger,
                             index=False,
                             unique=False,
                             nullable=True)
    elev = db.Column(db.Float,
                     index=False,
                     unique=False,
                     nullable=True)
    tp = db.Column(db.String,
                   index=False,
                   unique=False,
                   nullable=True)
    avg_speed = db.Column(db.Float,
                          index=False,
                          unique=False,
                          nullable=True)
    max_speed = db.Column(db.Float,
                          index=False,
                          unique=False,
                          nullable=True)
    calories = db.Column(db.Float,
                         index=False,
                         unique=False,
                         nullable=True)


class Parts(db.Model):
    """Data model for parts"""
    __tablename__ = 'parts'
    __table_args__ = {'sqlite_autoincrement': True}

    part_id = db.Column(db.Integer,
                        primary_key=True,
                        nullable=False,
                        unique=True)
    tp = db.Column(db.String,
                   index=False,
                   unique=False,
                   nullable=True)
    added = db.Column(db.Date,
                      index=False,
                      unique=False,
                      nullable=True)
    brand = db.Column(db.String,
                      index=False,
                      unique=False,
                      nullable=True)
    price = db.Column(db.Float,
                      index=False,
                      unique=False,
                      nullable=True)
    weight = db.Column(db.Float,
                       index=False,
                       unique=False,
                       nullable=True)
    size = db.Column(db.String,
                     index=False,
                     unique=False,
                     nullable=True)
    model = db.Column(db.String,
                      index=False,
                      unique=False,
                      nullable=True)
    bike = db.Column(db.String,
                     index=False,
                     unique=False,
                     nullable=True,
                     foreign_key='bikes.bike_id')
    retired = db.Column(db.Date,
                        index=False,
                        unique=False,
                        nullable=True)
    virtual = db.Column(db.Integer,
                        index=False,
                        unique=False,
                        nullable=True)


class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    __table_args__ = {'sqlite_autoincrement': True}

    maint_id = db.Column(db.Integer,
                         primary_key=True, 
                         nullable=False)
    part = db.Column(db.Integer,
                     index=False,
                     unique=False,
                     nullable=False,
                     foreign_key='parts.part_id')
    work = db.Column(db.String,
                     index=False,
                     unique=False,
                     nullable=True)
    date = db.Column(db.Date,
                     index=False,
                     unique=False,
                     nullable=True)

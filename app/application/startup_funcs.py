import sqlite3
import os


def init_new_db(db_path, schema_path, rider_name, rider_units):
    """Function to initialize a new DB using a pop-up dialogue"""
    create_db(db_path, schema_path)
    initialize_rider(db_path, rider_name, rider_units)


def initialize_rider(db_path, rider_name, rider_units):
    rider_values = (rider_name, rider_units)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT into riders (name, units)
                        VALUES (?, ?)""",
            rider_values,
        )


def create_db(db_path, schema_path):
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_path)

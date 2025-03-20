from zoneforge.db import db


# pylint: disable=too-few-public-methods
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(72), nullable=False)


# pylint: enable=too-few-public-methods

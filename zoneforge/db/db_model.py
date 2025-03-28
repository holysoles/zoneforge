from zoneforge.db import db

group_assign_roles = db.Table(
    "group_assign_role",
    db.Column(
        "group_id",
        db.Integer,
        db.ForeignKey("group.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "role_id",
        db.Integer,
        db.ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.UniqueConstraint("group_id", "role_id", name="unique_group_user"),
)


# pylint: disable=too-few-public-methods
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(72), nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey("group.id", ondelete="SET NULL"))


# pylint: disable=too-few-public-methods
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    users = db.relationship("User", backref="group")
    roles = db.relationship("Role", secondary=group_assign_roles, backref="groups")


# pylint: disable=too-few-public-methods
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)


# pylint: enable=too-few-public-methods

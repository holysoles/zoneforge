from flask_restx import Namespace, Resource, reqparse
import bcrypt
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin

from zoneforge.api import api_release_access
from zoneforge.db import db
from zoneforge.db.db_model import User

api = Namespace("idm", description="Identity Manager")

# Parsers
idm_parser = reqparse.RequestParser(bundle_errors=True)
idm_parser.add_argument("username", type=str, help="Missing username", required=True)
idm_parser.add_argument("password", type=str, help="Missing password", required=True)


@api.route("/user")
class UserResource(Resource):
    @api_release_access("user_read")
    def get(self):
        user_entities = db.paginate(db.select(User))

        return {
            "users": [
                {
                    "id": user.id,
                    "user_name": user.username,
                    "group": getattr(user.group, "name", "None"),
                }
                for user in user_entities
            ]
        }, 200

    @api_release_access("user_create")
    def post(self):
        args = idm_parser.parse_args()

        username = args.get("username")
        password = args.get("password")

        if not username or len(username) < 3:
            raise BadRequest("Username must be at least 3 characters long")

        if not password or len(password) < 6:
            raise BadRequest("Password must be at least 6 characters long")

        user_exists = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()

        if user_exists:
            raise Conflict("Username already exists")

        hashed_password = bcrypt.hashpw(
            password.encode(encoding="utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user = User(
            username=username,
            password=hashed_password,
        )

        db.session.add(user)
        db.session.commit()

        return {
            "id": user.id,
            "user_name": user.username,
            "message": "User created successfully",
        }, 201


@api.route("/user/<int:user_id>")
class SpecificUserResource(Resource):
    @api_release_access("user_update")
    def patch(self, user_id: int = None):
        username_idm_parser = idm_parser.copy()
        username_idm_parser.replace_argument(
            "username", type=str, help="Missing username", required=False
        )
        username_idm_parser.remove_argument("password")
        args = username_idm_parser.parse_args()

        username = args.get("username")

        if username and len(username) < 3:
            raise BadRequest("Username must be at least 3 characters long")

        if username:
            user_entity = db.session.execute(
                db.select(User).filter_by(username=username)
            ).scalar_one_or_none()

            if user_entity and user_entity.id == int(user_id):
                raise Conflict("This user already have this username")

            if user_entity:
                raise Conflict("Username already exist")

        current_user = db.get_or_404(User, user_id, description="User id not exist")
        current_user.username = username

        db.session.commit()

        return {"message": "User updated successfully"}, 200

    @api_release_access("user_delete")
    def delete(self, user_id: str = None):
        user_entity = db.get_or_404(User, user_id, description="User id not exist")

        db.session.delete(user_entity)
        db.session.commit()

        return {"message": "User deleted successfully"}, 200

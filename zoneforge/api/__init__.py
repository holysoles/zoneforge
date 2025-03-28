import jwt
from flask import current_app, g
from flask_restx import reqparse
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin

from zoneforge.db import db
from zoneforge.db.db_model import User

token_parser = reqparse.RequestParser(bundle_errors=True)
token_parser.add_argument(
    "Authorization",
    type=str,
    help="JWT token is missing",
    default="",
    location=["headers"],
)
token_parser.add_argument(
    "access_token", type=str, help="JWT token is missing", location=["cookies"]
)


# Decorator to validate JWT token and user permission
def release_access(permission: str = None):
    def wrapper(func):
        def decorated(*args, **kwargs):
            try:
                g.args = token_parser.parse_args()
                token = (
                    g.args.get("Authorization").split(" ")[-1]
                    or g.args.get("access_token")
                    or None
                )

                user_token_data = jwt.decode(
                    token, current_app.config["TOKEN_SECRET"], algorithms="HS256"
                )

                if permission and permission not in user_token_data["roles"]:
                    raise Forbidden(
                        "User do not have the required permissions to access this resource"
                    )

                current_user = db.get_or_404(User, user_token_data["id"])

                if not current_user:
                    raise NotFound("User not found")

                return func(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return {"message": "Token expired"}, 401

            except jwt.InvalidTokenError:
                return {"message": "Invalid token"}, 401

            except Forbidden as permission_denied:
                return {"message": permission_denied.description}, 403

            except NotFound as user_not_found:
                return {"message": user_not_found.description}, 404

        return decorated

    return wrapper

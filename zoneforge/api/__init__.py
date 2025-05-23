import jwt
from flask import current_app, g, flash, redirect, url_for
from flask_restx import reqparse
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin

from zoneforge.db import db
from zoneforge.db.db_model import User

from functools import wraps

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


# Function to validate WT token and user permission
def _verify_jwt_and_permissions(permission: str = None):
    args = token_parser.parse_args()
    token = args.get("Authorization").split(" ")[-1] or args.get("access_token") or None

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

    return user_token_data


# Decorator to handle API access
def api_release_access(permission: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                _verify_jwt_and_permissions(permission)

                return func(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return {"message": "Token expired"}, 401

            except jwt.InvalidTokenError:
                return {"message": "Invalid token"}, 401

            except Forbidden as permission_denied:
                return {"message": permission_denied.description}, 403

            except NotFound as user_not_found:
                return {"message": user_not_found.description}, 404

        return wrapper

    return decorator


# Decorator to handle APP access
def app_release_access(permission: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                current_user = _verify_jwt_and_permissions(permission)
                g.current_user = current_user

                return func(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                flash("Session expired.", "error")
                return redirect(url_for("login"))

            except jwt.InvalidTokenError:
                flash("Invalid session.", "error")
                return redirect(url_for("login"))

            except Forbidden:
                flash(
                    "You don’t have permission to access this page or perform this action.",
                    "error",
                )
                return redirect(url_for("login"))

            except NotFound:
                flash("User not found.", "error")
                return redirect(url_for("login"))

        return wrapper

    return decorator

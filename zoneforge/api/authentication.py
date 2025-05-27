from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from flask import current_app
from flask_restx import Namespace, Resource, reqparse
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
import zoneforge.db.db_model as model
from zoneforge.db import db
from zoneforge.api import token_parser

api = Namespace("auth", description="Authentication operations")

# Parsers
login_parser = reqparse.RequestParser(bundle_errors=True)
login_parser.add_argument("username", type=str, help="Missing username", required=True)
login_parser.add_argument("password", type=str, help="Missing password", required=True)

token_parser.add_argument(
    "refresh_token", type=str, help="JWT token is missing", location=["cookies"]
)


def _generate_token(user_id):
    try:
        user_entity = db.get_or_404(
            model.User, user_id, description=f"User id '{user_id}' not found"
        )

        group_roles = (
            [role.name for role in user_entity.group.roles] if user_entity.group else []
        )

        token_payload = {
            "username": user_entity.username,
            "roles": group_roles,
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30),
        }

        refresh_token_payload = {
            "id": user_entity.id,
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=60),
        }

        token_payload.update(refresh_token_payload)

        token = jwt.encode(
            token_payload, current_app.config["TOKEN_SECRET"], algorithm="HS256"
        )

        refresh_token = jwt.encode(
            refresh_token_payload,
            current_app.config["REFRESH_TOKEN_SECRET"],
            algorithm="HS256",
        )

        return {"token": token, "refresh_token": refresh_token}

    except NotFound as user_not_found:
        return {"message": user_not_found.description}, 404


@api.route("/login")
class LoginResource(Resource):
    def post(self):
        try:
            args = login_parser.parse_args()
            username = args.get("username")
            password = args.get("password").encode(encoding="utf-8")

            user_entity = db.one_or_404(
                db.select(model.User).filter_by(username=username),
                description=f"User '{username}' not found",
            )

            if not user_entity or not bcrypt.checkpw(
                password, user_entity.password.encode(encoding="utf-8")
            ):
                raise Unauthorized("Username and password not match")

            return _generate_token(user_entity.id), 200

        except NotFound as user_not_found:
            return {"message": user_not_found.description}, 404

        except Unauthorized as wrong_credentials:
            return {"message": wrong_credentials.description}, 401


@api.route("/refresh")
class RefreshTokenResource(Resource):
    def post(self):
        args = token_parser.parse_args()
        token = (
            args.get("Authorization").split(" ")[-1]
            or args.get("refresh_token")
            or None
        )

        user_refresh_token_data = jwt.decode(
            token, current_app.config["REFRESH_TOKEN_SECRET"], algorithms="HS256"
        )

        return _generate_token(user_refresh_token_data["id"]), 200


@api.route("/signup")
class SignupResource(Resource):
    def post(self):
        try:
            args = login_parser.parse_args()

            username = args.get("username")
            password = args.get("password")

            if not username or len(username) < 3:
                raise BadRequest("Username must be at least 3 characters long")

            if not password or len(password) < 6:
                raise BadRequest("Password must be at least 6 characters long")

            user_exists = db.session.execute(
                db.select(model.User).filter_by(username=username)
            ).scalar_one_or_none()

            if user_exists:
                raise Conflict("Username already exists")

            hashed_password = bcrypt.hashpw(
                password.encode(encoding="utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            user = model.User(
                username=username,
                password=hashed_password,
            )

            db.session.add(user)
            db.session.commit()

            return {"message": "User created successfully"}, 200

        except BadRequest as credential_error:
            return {"message": credential_error.description}, 400

        except Conflict as user_exist:
            return {"message": user_exist.description}, 409

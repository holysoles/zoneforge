from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from flask import current_app
from flask_restx import Namespace, Resource, reqparse
from werkzeug.exceptions import *

import zoneforge.db.db_model as model
from zoneforge.db import db
from functools import wraps

api = Namespace('auth', description='Authentication operations')

# Parsers
login_parser = reqparse.RequestParser(bundle_errors=True)
login_parser.add_argument('username', type=str, help='Missing username', required=True)
login_parser.add_argument('password', type=str, help='Missing password', required=True)

token_parser = reqparse.RequestParser(bundle_errors=True)
token_parser.add_argument('Authorization', type=str, help='JWT token is missing', required=True, location=['cookies', 'headers'])

# Decorator to validate JWT token
def validate_token(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            args = token_parser.parse_args()
            token = args.get('Authorization').split(" ")[-1]

            user_token_data = jwt.decode(
                token,
                current_app.config['TOKEN_SECRET'],
                algorithms="HS256"
            )

            current_user = db.get_or_404(model.User, user_token_data["id"])

            if not current_user:
                raise NotFound("User not found")

            return func(*args, **kwargs)

        except BadRequest as bad_request:
            if hasattr(bad_request, "data") and "Authorization" in bad_request.data["errors"]:
                return {"message": "Missing JWT token"}, 401

            return {"message": bad_request.description}, 400

        except jwt.ExpiredSignatureError:
            return {"message": "Token expired"}, 401

        except jwt.InvalidTokenError:
            return {"message": "Invalid token"}, 401

        except NotFound as user_not_found:
            return {"message": user_not_found.description}, 404

        except Exception as error:
            return {"message": str(error)}, 400

    return decorated

def _generate_token(user_id):
    try:
        user_entity = db.get_or_404(
            model.User,
            user_id,
            description=f"User id '{user_id}' not found"
        )

        token_payload = {
            "username": user_entity.username,
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30)
        }

        refresh_token_payload = {
            "id": user_entity.id,
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=60)
        }

        token_payload.update(refresh_token_payload)

        token = jwt.encode(
            token_payload,
            current_app.config['TOKEN_SECRET'],
            algorithm="HS256"
        )

        refresh_token = jwt.encode(
            refresh_token_payload,
            current_app.config['REFRESH_TOKEN_SECRET'],
            algorithm="HS256"
        )

        return {
            "token": token,
            "refresh_token": refresh_token
        }

    except NotFound as user_not_found:
            return {"message": user_not_found.description}, 404

    except Exception as error:
            return {"message": str(error)}, 400

@api.route('/login')
class LoginResource(Resource):
    def post(self):
        try:
            args = login_parser.parse_args()
            username = args.get('username')
            password = args.get('password').encode(encoding="utf-8")

            user_entity = db.one_or_404(
                db.select(model.User).filter_by(username=username),
                description=f"User '{username}' not found"
            )

            if not user_entity or not bcrypt.checkpw(password, user_entity.password.encode(encoding="utf-8")):
                raise Unauthorized("Username and password not match")

            return _generate_token(user_entity.id), 200

        except BadRequest as bad_request:
            if hasattr(bad_request, "data") and "username" in bad_request.data["errors"]:
                return {"message": "Missing username field"}, 400

            if hasattr(bad_request, "data") and "password" in bad_request.data["errors"]:
                return {"message": "Missing password field"}, 400

            return {"message": bad_request.description}, 400

        except NotFound as user_not_found:
            return {"message": user_not_found.description}, 404

        except Unauthorized as wrong_credentials:
            return {"message": wrong_credentials.description}, 401

        except Exception as error:
            return {"message": str(error)}, 400

@api.route('/refresh')
class RefreshTokenResource(Resource):
    def post(self):
        try:
            args = token_parser.parse_args()
            token = args.get('Authorization').split(" ")[-1]

            user_refresh_token_data = jwt.decode(
                token,
                current_app.config['REFRESH_TOKEN_SECRET'],
                algorithms="HS256"
            )

            return _generate_token(user_refresh_token_data["id"]), 200

        except BadRequest as bad_request:
            if hasattr(bad_request, "data") and "Authorization" in bad_request.data["errors"]:
                return {"message": "Missing JWT token"}, 400

            return {"message": bad_request.description}, 400

        except Exception as error:
            return {"message": str(error)}, 400

@api.route('/signup')
class SignupResource(Resource):
    def post(self):
        try:
            args = login_parser.parse_args()

            username = args.get('username')
            password = args.get('password')

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
                username = username,
                password = hashed_password,
            )

            db.session.add(user)
            db.session.commit()

            return {"message": "User created successfully"}, 200

        except BadRequest as bad_request:
            if hasattr(bad_request, "data") and "username" in bad_request.data["errors"]:
                return {"message": "Missing username field"}, 400

            if hasattr(bad_request, "data") and "password" in bad_request.data["errors"]:
                return {"message": "Missing password field"}, 400

            return {"message": bad_request.description}, 400

        except Conflict as user_exist:
            return {"message": user_exist.description}, 409

        except Exception as error:
            return {"message": str(error)}, 400

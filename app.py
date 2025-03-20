import os
import logging
import sys
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_restx import Api
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_minify import minify
import zoneforge.modal_data
from zoneforge.api.status import api as ns_status
from zoneforge.api.types import api as ns_types
from zoneforge.api.types import RecordTypeResource
from zoneforge.api.zones import api as ns_zone
from zoneforge.api.zones import DnsZone, get_zones
from zoneforge.api.records import api as ns_record
from zoneforge.api.records import DnsRecord
from zoneforge.api.authentication import api as ns_auth
from zoneforge.api.authentication import LoginResource, SignupResource
from zoneforge.db import db


def get_logging_conf() -> dict:
    log_config = {}
    log_config["level"] = os.environ.get("LOG_LEVEL", "WARNING").upper()
    log_config["format"] = (
        "%(levelname)s [%(filename)-s%(funcName)s():%(lineno)s]: %(message)s"
    )
    if not os.environ.get("CONTAINER", False):
        log_config["format"] = f"[%(asctime)s] {log_config['format']}"
    log_config["handlers"] = [logging.StreamHandler(sys.stdout)]
    return log_config


def create_app():
    # Flask App setup
    app = Flask(__name__, static_folder="static", static_url_path="")

    # Configuration with environment variables and defaults
    log_config = get_logging_conf()
    logging.basicConfig(**log_config)

    try:
        git_tag = (
            subprocess.run(
                ["git", "describe", "--tags"], capture_output=True, check=False
            )
            .stdout.decode("utf-8")
            .rstrip("\n")
        )
    except FileNotFoundError:
        git_tag = None
    app.config["VERSION"] = os.environ.get("VERSION", git_tag)
    app.config["ZONE_FILE_FOLDER"] = os.environ.get(
        "ZONE_FILE_FOLDER", "./lib/examples"
    )
    app.config["DEFAULT_ZONE_TTL"] = os.environ.get("DEFAULT_ZONE_TTL", 86400)
    app.config["AUTH_ENABLED"] = (
        os.environ.get("AUTH_ENABLED", "false").lower() == "true"
    )
    app.config["SECRET_KEY"] = os.environ.get("AUTH_SECRET_KEY", "secret_key")
    app.config["TOKEN_SECRET"] = os.environ.get("AUTH_TOKEN_SECRET", "token_secret")
    app.config["REFRESH_TOKEN_SECRET"] = os.environ.get(
        "AUTH_REFRESH_TOKEN_SECRET", "refresh_token_secret"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "AUTH_DB_URI", "sqlite:///zoneinfo.db"
    )

    if app.config["AUTH_ENABLED"]:
        logging.info("authentication enabled, setting up database")
        db.init_app(app)
        with app.app_context():
            db.create_all()

    minify(app=app, html=True, js=True, cssless=True, static=True)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    # API Setup
    api = Api(app, prefix="/api", doc="/api", validate=True)

    @app.route("/", methods=["GET"])
    def home():
        zf_zone = DnsZone()
        try:
            zones = zf_zone.get()
        # generic except to actually let the homepage render, even if internal error
        except:  # pylint: disable=bare-except
            zones = []
        zone_create_defaults = (
            zoneforge.modal_data.ZONE_DEFAULTS
            | zoneforge.modal_data.ZONE_PRIMARY_NS_DEFAULTS
        )
        return render_template(
            "home.html.j2",
            zones=zones,
            modal=zoneforge.modal_data.ZONE_CREATION,
            modal_api="/api/zones",
            modal_default_values=zone_create_defaults,
        )

    @app.route("/zone/<string:zone_name>", methods=["GET"])
    def zone(zone_name):
        zone = get_zones(zone_name=zone_name)[0].to_response()
        zf_record = DnsRecord()
        records = zf_record.get(zone_name=zone_name)
        current_zone_data = {
            "name": zone_name,
            "soa_ttl": zone["soa"]["ttl"],
            "admin_email": zone["soa"]["data"]["rname"],
            "refresh": zone["soa"]["data"]["refresh"],
            "retry": zone["soa"]["data"]["retry"],
            "expire": zone["soa"]["data"]["expire"],
            "minimum": zone["soa"]["data"]["minimum"],
            "primary_ns": zone["soa"]["data"]["mname"],
        }
        record_types_list = RecordTypeResource().get()
        user_sort = request.args.get("sort", "name")
        user_sort_order = request.args.get("sort_order", "desc")
        return render_template(
            "zone.html.j2",
            zone=zone,
            modal=zoneforge.modal_data.ZONE_EDIT,
            modal_default_values=current_zone_data,
            records=records,
            record_types=record_types_list,
            record_sort=user_sort,
            record_sort_order=user_sort_order,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            login_response = LoginResource().post()

            if login_response[1] != 200:
                flash(login_response[0])

                return render_template("login.html.j2")

            return redirect(url_for("home"))
        return render_template("login.html.j2")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            signup_response = SignupResource().post()

            flash(signup_response[0])

            if signup_response[1] != 200:

                return render_template("signup.html.j2")

            return redirect(url_for("login"))
        return render_template("signup.html.j2")

    api.add_namespace(ns_status)
    api.add_namespace(ns_zone)
    api.add_namespace(ns_record)
    api.add_namespace(ns_types)
    api.add_namespace(ns_auth)

    return app


if __name__ == "__main__":
    dev = create_app()
    dev.run()
else:
    production = create_app()

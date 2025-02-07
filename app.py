from flask import Flask, render_template, request, redirect, url_for, flash
from flask_restx import Api
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_minify import minify
import zoneforge.zf_api as zf_api
import zoneforge.authentication as auth
from zoneforge.modal_data import *
import os
from db import db

# Flask App setup
app = Flask(__name__, static_folder='static', static_url_path='')

# Configuration with environment variables and defaults
app.config['ZONE_FILE_FOLDER'] = os.environ.get('ZONE_FILE_FOLDER', './lib/examples')
app.config['DEFAULT_ZONE_TTL'] = int(os.environ.get('DEFAULT_ZONE_TTL', '86400'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret_key')
app.config['TOKEN_SECRET'] = os.environ.get('TOKEN_SECRET', 'token_secret')
app.config['REFRESH_TOKEN_SECRET'] = os.environ.get('REFRESH_TOKEN_SECRET', 'refresh_token_secret')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///zoneinfo.db')
db.init_app(app)

with app.app_context():
    db.create_all()

minify(app=app, html=True, js=True, cssless=True, static=True)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
# API Setup
api = Api(app, prefix= '/api', doc='/api',)

@app.route("/", methods=['GET'])
def home():
    zf_zone = zf_api.ZoneResource()
    try:
        zones = zf_zone.get()
    except:
        zones = []
    zone_create_defaults = ZONE_DEFAULTS | ZONE_PRIMARY_NS_DEFAULTS
    return render_template('home.html.j2', zones=zones, modal=ZONE_CREATION, modal_api='/api/zone', modal_default_values=zone_create_defaults)

@app.route("/zone/<string:zone_name>", methods=['GET'])
def zone(zone_name):
    zone = zf_api.get_zones(zone_name=zone_name)[0].to_response()
    zf_record = zf_api.RecordResource()
    records = zf_record.get(zone_name=zone_name)
    current_zone_data = {
        "name": zone_name,
        "soa_ttl": zone['soa']['ttl'],
        "admin_email": zone['soa']['data']['rname'],
        "refresh": zone['soa']['data']['refresh'],
        "retry": zone['soa']['data']['retry'],
        "expire": zone['soa']['data']['expire'],
        "minimum": zone['soa']['data']['minimum'],
        "primary_ns": zone['soa']['data']['mname'],
    }
    record_types = zf_api.RecordTypeResource()
    record_types = record_types.get()
    user_sort = request.args.get("sort", "name")
    user_sort_order = request.args.get("sort_order", "desc")
    return render_template('zone.html.j2', zone=zone, modal=ZONE_EDIT, modal_default_values=current_zone_data, records=records, record_types=record_types, record_sort=user_sort, record_sort_order=user_sort_order)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_response = auth.LoginResource().post()

        if login_response[1] != 200:
            flash(login_response[0])

            return render_template('login.html.j2')

        return redirect(url_for('home'))
    return render_template('login.html.j2')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        signup_response = auth.SignupResource().post()

        flash(signup_response[0])

        if signup_response[1] != 200:

            return render_template('signup.html.j2')

        return redirect(url_for('login'))
    return render_template('signup.html.j2')


api.add_resource(zf_api.StatusResource, '/status')
api.add_resource(zf_api.ZoneResource, '/zone', '/zone/<string:zone_name>')
api.add_resource(zf_api.RecordResource, '/zone/<string:zone_name>/record', '/zone/<string:zone_name>/record/<string:record_name>')
api.add_resource(zf_api.RecordTypeResource, '/types/recordtype', '/types/recordtype/<string:record_type>')
api.add_resource(auth.LoginResource, '/login')
api.add_resource(auth.RefreshTokenResource, '/refresh')
api.add_resource(auth.SignupResource, '/signup')

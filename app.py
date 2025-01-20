from flask import Flask, render_template
from flask_restx import Api
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_minify import minify
import zoneforge.zf_api as zf_api
from zoneforge.modal_data import *
import os

# Flask App setup
app = Flask(__name__, static_folder='static', static_url_path='')

# Configuration with environment variables and defaults
app.config['ZONE_FILE_FOLDER'] = os.environ.get('ZONE_FILE_FOLDER', './lib/examples')
app.config['DEFAULT_ZONE_TTL'] = int(os.environ.get('DEFAULT_ZONE_TTL', '86400'))

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
    zf_record = zf_api.RecordResource()
    records = zf_record.get(zone_name=zone_name)
    soa = zf_record.get(zone_name=zone_name, record_type='SOA')[0]
    current_zone_data = {
        "name": zone_name,
        "soa_ttl": soa["ttl"],
        "admin_email": soa["data"]["email"],
        "refresh": soa["data"]["refresh"],
        "retry": soa["data"]["retry"],
        "expire": soa["data"]["expire"],
        "minimum": soa["data"]["minimum"],
        "primary_ns": soa["data"]["primary_ns"],

    }
    return render_template('zone.html.j2', zone=zone_name, soa=soa, records=records, modal=ZONE_EDIT, modal_api='/api/zone', modal_default_values=current_zone_data)

api.add_resource(zf_api.StatusResource, '/status')
api.add_resource(zf_api.ZoneResource, '/zone', '/zone/<string:zone_name>')
api.add_resource(zf_api.RecordResource, '/zone/<string:zone_name>/record', '/zone/<string:zone_name>/record/<string:record_name>')

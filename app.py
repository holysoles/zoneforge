from os import listdir, getenv
from os.path import join, splitext
from flask import Flask, request, Response, render_template, url_for
from flask_restful import Api, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_minify import minify
import zoneforge.zf_api as zf_api

# Flask App setup
app = Flask(__name__, static_folder='static', static_url_path='')
minify(app=app, html=True, js=True, cssless=True, static=True)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
# API Setup
api_errors = zf_api.ZFErrors.dict
api = Api(app, "/api", errors=api_errors)


@app.route("/", methods=['GET'])
def home():
    zf_zone = zf_api.ZoneResource()
    zones = zf_zone.get()
    return render_template('home.html.j2', zones=zones)

@app.route("/zone/<string:zone_name>", methods=['GET'])
def zone(zone_name):
    zf_record = zf_api.RecordResource()
    records = zf_record.get(zone_name)
    return render_template('zone.html.j2', zone=zone_name, records=records)

api.add_resource(zf_api.StatusResource, '/status')
api.add_resource(zf_api.ZoneResource, '/zone', '/zone/<string:zone_name>')
api.add_resource(zf_api.RecordResource, '/zone/<string:zone_name>/record', '/zone/<string:zone_name>/record/<string:record_name>')

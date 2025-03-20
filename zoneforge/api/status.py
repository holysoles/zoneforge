from flask_restx import Resource, Namespace, fields
from flask import current_app

api = Namespace("status", description="Retrieve server status information")

status_res_fields = api.model(
    "ServerStatus",
    {
        "running": fields.Boolean(
            description="Whether or not the API server is running"
        ),
    },
)

version_res_fields = api.model(
    "ServerVersion",
    {
        "version": fields.String(
            description="Whether or not the API server is running"
        ),
    },
)


@api.route("")
class ServerStatus(Resource):
    @api.marshal_with(status_res_fields)
    def get(self):
        """
        Gets the current webserver status.
        """
        return {"running": True}


@api.route("/version")
class ServerVersion(Resource):
    @api.marshal_with(version_res_fields)
    def get(self):
        """
        Gets the current webserver's version.
        """
        return {"version": current_app.config["VERSION"]}

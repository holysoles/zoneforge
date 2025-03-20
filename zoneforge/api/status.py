from flask_restx import Resource, Namespace, fields

api = Namespace("status", description="Retrieve server status information")

status_res_fields = api.model(
    "ServerStatus",
    {
        "running": fields.Boolean(
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

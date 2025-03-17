from flask_restx import Resource, Namespace, fields
from zoneforge.core import get_all_record_types, get_record_type_map
from werkzeug.exceptions import *

api = Namespace('types', description='Retrieve information about DNS resource types')

type_res_fields = api.model('RecordDataType', {
    'type': fields.String(description="The Record Data Type to retrieve", example="CNAME"),
    'fields': fields.List(fields.String, example=['target']),
})

@api.route('/recordtype')
class RecordTypeResource(Resource):
    @api.marshal_with(type_res_fields, as_list=True)
    def get(self):
        """
        Gets a list of all DNS record types and their associated fields.
        """
        record_types = get_all_record_types()
        return record_types

@api.route('/recordtype/<string:record_type>')
class SpecificRecordTypeResource(Resource):
    @api.marshal_with(type_res_fields)
    def get(self, record_type: str = None):
        """
        Gets a specific DNS record type and its associated fields.
        """
        return get_record_type_map(record_type_name=record_type)

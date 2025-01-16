from werkzeug.exceptions import *

class ZoneNotFoundError(HTTPException):
    pass
class ZoneAlreadyExists(HTTPException):
    pass

class RecordNotFoundError(HTTPException):
    pass
class RecordAlreadyExists(HTTPException):
    pass
from enum import Enum

INEXISTENT_INTENT = "UQL:INEXISTENT_INTENT"  # requested intent was not found
NO_INTENT = "UQL:NO_INTENT"  # intent wasn't passed on request
INVALID_REQUEST_HANDLER_OUTPUT = "UQL:INVALID_REQUEST_HANDLER_OUTPUT"  # output from intent handler is invalid; ie. not a list or dict or none
INVALID_REQUEST_BODY = "UQL:INVALID_REQUEST_BODY"
MISSING_REQUIRED_ARGUMENT = (
    "UQL:MISSING_REQUIRED_ARGUMENT"  # call to intents missing argument
)
DEFAULT_ON_REQUIRED_ARGS = (
    "UQL:DEFAULT_ON_REQUIRED_ARGS"  # required args should not have default values
)
UNKNOWN_ARGS = "UQL:UNKNOWN_ARGS"  # unknown argument in request
OBJECT_NOT_FOUND = "UQL:OBJECT_NOT_FOUND"


ALL_COLUMNS = "ALL_COLUMNS"
ALL_ROWS = "ALL_ROWS"


class RelationshipTypes(Enum):
    LIST = 1
    OBJECT = 2


class ModelOperations(Enum):
    INSERT = "INSERT"
    SELECT = "SELECT"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    SELECT_MANY = "SELECT_MANY"
    # INSERT_MANY = "INSERT_MANY"
    # DELETE_MANY = "DELETE_MANY"
    # UPDATE_MANY = "UPDATE_MANY"

    @staticmethod
    def all():
        return [
            ModelOperations.INSERT,
            ModelOperations.SELECT,
            ModelOperations.DELETE,
            ModelOperations.UPDATE,
            ModelOperations.SELECT_MANY,
            # ModelOperations.INSERT_MANY,
            # ModelOperations.DELETE_MANY,
            # ModelOperations.UPDATE_MANY,
        ]

    @staticmethod
    def readonly():
        return [ModelOperations.SELECT, ModelOperations.SELECT_MANY]

    @staticmethod
    def readonly_and_single_write():
        return [
            ModelOperations.SELECT,
            ModelOperations.SELECT_MANY,
            ModelOperations.INSERT,
            ModelOperations.UPDATE,
            ModelOperations.DELETE,
        ]

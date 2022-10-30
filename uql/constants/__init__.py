from enum import Enum


class CellFlags(Enum):
    ALL = 1


class RelationshipTypes(Enum):
    LIST = 1
    OBJECT = 2


class ModelOperations(Enum):
    SELECT_ONE = 0
    SELECT_MANY = 1
    INSERT = 2
    INSERT_MANY = 3
    UPDATE = 4
    UPDATE_MANY = 5
    DELETE = 6
    DELETE_MANY = 7

    @staticmethod
    def all():
        return [
            ModelOperations.SELECT_ONE,
            ModelOperations.SELECT_MANY,
            ModelOperations.INSERT,
            ModelOperations.INSERT_MANY,
            ModelOperations.UPDATE,
            ModelOperations.UPDATE_MANY,
            ModelOperations.DELETE,
            ModelOperations.DELETE_MANY,
        ]

    @staticmethod
    def readonly():
        return [ModelOperations.SELECT_ONE, ModelOperations.SELECT_MANY]

    @staticmethod
    def readonly_and_single_write():
        return [
            ModelOperations.SELECT_ONE,
            ModelOperations.SELECT_MANY,
            ModelOperations.INSERT,
            ModelOperations.UPDATE,
            ModelOperations.DELETE,
        ]

from uql.model import ModelConfig
from uql.model import PartialUpdateTyping
from uql.model import ModelPermissionTyping
from uql.model import SelectPermissionTyping
from uql.model import UpdatePermissionTyping
from uql.model import DeletePermissionTyping
from uql.model import InsertPermissionTyping
from uql.config import UQLConfig
from uql.constants import CellFlags
from uql.constants import ModelOperations
from uql.constants import errors as errorConstants
from uql.constants import types
from uql.utils import templates as t
from uql.utils.query import makeQuery
from uql.exceptions import RequestHandlingError

from rest_framework.request import Request

from django.db import transaction
from django.db.models import Field, Model
from django.db.utils import IntegrityError

from . import IntentFunction
import typing

ModelOperationPermission: typing.TypeAlias = (
    SelectPermissionTyping
    | UpdatePermissionTyping
    | InsertPermissionTyping
    | DeletePermissionTyping
)

ModelOperationKeys: typing.TypeAlias = (
    typing.Literal["select"]
    | typing.Literal["insert"]
    | typing.Literal["update"]
    | typing.Literal["delete"]
)


class ModelIntent:
    def __init__(self, rootConfig: type[UQLConfig], modelConfig: ModelConfig) -> None:
        self.modelConfig = modelConfig
        self.rootConfig = rootConfig

    @staticmethod
    def getUserIdFromRequest(request: Request) -> types.Pk | None:
        return getattr(request.user, "id", None)

    @staticmethod
    def getPermission(
        role: str,
        operation: ModelOperationKeys,
        permissions: dict[
            str, typing.Callable[[types.Pk | None], ModelPermissionTyping]
        ],
        userId: str | int | None = None,
    ) -> tuple[ModelPermissionTyping, ModelOperationPermission]:

        # get permission config
        # pass the user id here since we're trying to get the rows
        permission = permissions.get(role, lambda x: None)(userId)
        permissionError = PermissionError(
            f"User{'({id})'.format({id: userId}) if userId else ''} with role: '{role}' has no {operation} permission",
            401,
        )

        if not permission:
            raise permissionError

        # operation permission
        operationPermission: ModelOperationPermission | None = permission.get(operation)

        if not operationPermission:
            raise permissionError

        return (permission, operationPermission)

    def find(self, request: Request, args: dict):
        """returns a single object from models

        Args:
            request (Request): _description_
            args (dict): _description_

        Raises:
            Interruption: _description_

        Returns:
            _type_: _description_
        """
        where = args.get("where")
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        Sr = self.modelConfig.createSerializerClass(role)

        selectPermission = typing.cast(
            SelectPermissionTyping,
            ModelIntent.getPermission(
                role,
                "select",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            )[1],
        )

        query = makeQuery(where) if where else None

        models = (
            self.modelConfig.model.objects.all()
            if selectPermission["row"] == CellFlags.ALL
            else self.modelConfig.model.objects.filter(selectPermission["row"])
        )

        instance = models.get(query) if query else models.first()
        return Sr(instance).data

    def selectMany(self, request: Request, args: dict):
        """Select items of a model.

        Args:
            request (Request): _description_
            args (dict): _description_

        Raises:
            Interruption: _description_

        Returns:
            _type_: _description_
        """
        where = args.get("where")
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        Sr = self.modelConfig.createSerializerClass(role)

        selectPermission = typing.cast(
            SelectPermissionTyping,
            ModelIntent.getPermission(
                role,
                "select",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            )[1],
        )

        query = makeQuery(where) if where else None
        models = (
            self.modelConfig.model.objects.all()
            if selectPermission["row"] == CellFlags.ALL
            else self.modelConfig.model.objects.filter(selectPermission["row"])
        )

        models = models.filter(query) if query else models
        return Sr(models, many=True).data

    def insert(self, request: Request, args: dict[str, typing.Any]):
        obj: dict[str, typing.Any] = args["object"]  # required

        # get role and permission config
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)

        _, insertPermission = typing.cast(
            tuple[ModelPermissionTyping, InsertPermissionTyping],
            ModelIntent.getPermission(
                role,
                "insert",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            ),
        )

        checkDefault = lambda request, params: True
        insertPermission.setdefault("check", checkDefault)
        insertPermission.setdefault("requiredFields", [])

        if not insertPermission.get("check", checkDefault)(request, obj):
            raise PermissionError("Unauthorized insertion", 401)

        # required fields should be a subset of insertable column
        if not (
            insertPermission["column"] == CellFlags.ALL
            or set(
                typing.cast(list[str], insertPermission.get("requiredFields"))
            ).issubset(insertPermission["column"])
        ):
            raise Exception(
                "insert.requiredFields should be a subset of insert.columns", 500
            )

        # check if required field's in obj
        if not set(
            typing.cast(list[str], insertPermission.get("requiredFields"))
        ).issubset(obj.keys()):
            raise Exception(
                f"requires fields ({', '.join(typing.cast(list[str], insertPermission.get('requiredFields')))})",
                500,
            )

        # check if user only included permitted colums in obj
        fields = (
            [
                field.name
                for field in self.modelConfig.model._meta.get_fields()
                if isinstance(field, Field)
            ]
            + [fk for fk in self.modelConfig.foreignKeys.keys()]
            if insertPermission["column"] == CellFlags.ALL
            else insertPermission["column"]
        )

        for key in obj.keys():
            if not (key in fields):
                raise RequestHandlingError(
                    f'cannot insert "{key}" in {self.modelConfig.name}',
                    errorCode=errorConstants.UNKNOWN_ARGS,
                    statusCode=400,
                )

            # foriegn keys need to be passed by object
            # we might have an input that tries to insert author="author-pk" in Book modek
            # but book.author has to be an Object not a string. so we check to see if Book config
            # has any foriegn key config attached names author, then we map "author-pk"...
            # to it's respective object
            fk = self.modelConfig.foreignKeys.get(key)
            if fk:
                # if key is a foriegn key, change the string or integer pk to an item
                # that correspond to its model object
                # obj[key] = fk.getObject(obj[key])
                obj[key] = fk["model"].objects.get(obj[key])

        try:
            # create model
            model = self.modelConfig.model(**obj)
            model.save()

            # get model data from select realizers
            Sr = self.modelConfig.createSerializerClass(role)
            return Sr(model).data

        except Exception as e:
            raise RequestHandlingError(
                e.args[0] if len(e.args) > 0 else "Unknown error",
                errorCode=e.__class__.__name__,
                statusCode=400,
            )

    def insertMany(self, request: Request, args: dict):
        objects: list[dict[str, typing.Any]] = args["objects"]  # required

        # get role and permission config
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)

        # get insert permission
        _, insertPermission = typing.cast(
            tuple[ModelPermissionTyping, InsertPermissionTyping],
            ModelIntent.getPermission(
                role,
                "insert",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            ),
        )

        checkDefault = lambda request, params: True
        insertPermission.setdefault("check", checkDefault)
        insertPermission.setdefault("requiredFields", [])

        if not all(
            [
                insertPermission.get("check", checkDefault)(request, param)
                for param in objects
            ]
        ):
            raise PermissionError("Unauthorised insertion", 401)

        # get model data from select realizers
        Sr = self.modelConfig.createSerializerClass(role)

        # required fields should be a subset of insertable column
        if not (
            insertPermission["column"] == CellFlags.ALL
            or set(
                typing.cast(list[str], insertPermission.get("requiredFields"))
            ).issubset(insertPermission["column"])
        ):
            raise Exception(
                "insert.requiredFields should be a subset of insert.columns", 500
            )

        # check if required field's in each object
        if not all(
            [
                set(
                    typing.cast(list[str], insertPermission.get("requiredFields"))
                ).issubset(obj.keys())
                for obj in objects
            ]
        ):
            raise Exception(
                f"requires fields ({', '.join(typing.cast(list[str], insertPermission.get('requiredFields')))})"
            )

        # check if user only included permitted colums in each object
        fields = (
            [
                field.name
                for field in self.modelConfig.model._meta.get_fields()
                if isinstance(field, Field)
            ]
            + [fk for fk in self.modelConfig.foreignKeys.keys()]
            if insertPermission["column"] == CellFlags.ALL
            else insertPermission["column"]
        )

        res = []  # result

        try:
            with transaction.atomic():
                for obj in objects:
                    for key in obj.keys():
                        if not (key in fields):
                            raise RequestHandlingError(
                                f'cannot insert "{key}" in {self.modelConfig.name}',
                                errorCode=errorConstants.UNKNOWN_ARGS,
                                statusCode=400,
                            )

                        # foriegn keys need to be passed by object
                        # we might have an input that tries to insert author="author-pk" in Book modek
                        # but book.author has to be an Object not a string. so we check to see if Book config
                        # has any foriegn key config attached names author, then we map "author-pk"...
                        # to it's respective object
                        fk = self.modelConfig.foreignKeys.get(key)
                        if fk:
                            # if key is a foriegn key, change the string or integer pk to an item
                            # that correspond to its model object
                            obj[key] = fk["model"].objects.get(obj[key])

                    # create model
                    model = self.modelConfig.model(**obj)
                    model.save()

                    res.append(model)

        except Exception as e:
            raise RequestHandlingError(
                e.args[0] if len(e.args) > 0 else "Unknown error",
                errorCode=e.__class__.__name__,
                statusCode=400,
            )

        return Sr(res, many=True).data

    def update(self, request: Request, args):
        args = typing.cast(PartialUpdateTyping, args)
        partial: dict = args["partial"]  # required
        pk: types.Pk = args["pk"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)

        _, updatePermission = typing.cast(
            tuple[ModelPermissionTyping, UpdatePermissionTyping],
            ModelIntent.getPermission(
                role,
                "update",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            ),
        )
        checkDefault = lambda req, partial: True
        updatePermission.setdefault("check", checkDefault)

        if not updatePermission.get("check", checkDefault)(
            request, {"pk": pk, "partial": partial}
        ):
            raise PermissionError("Unauthorized mutation", 401)

        Sr = self.modelConfig.createSerializerClass(role)

        # fetch all the rows that can be updated by the client
        models = (
            self.modelConfig.model.objects.all()
            if updatePermission["row"] == CellFlags.ALL
            else self.modelConfig.model.objects.filter(updatePermission["row"])
        )

        try:
            obj: Model = models.get(pk=pk)

            # check if user only included permitted colums in obj
            fields = (
                [
                    field.name
                    for field in self.modelConfig.model._meta.get_fields()
                    if isinstance(field, Field)
                ]
                + [fk for fk in self.modelConfig.foreignKeys.keys()]
                if updatePermission["column"] == CellFlags.ALL
                else updatePermission["column"]
            )

            for key, value in partial.items():
                if not (key in fields):
                    raise RequestHandlingError(
                        f'cannot update "{key}" in {self.modelConfig.name}',
                        errorCode="",
                        statusCode=400,
                    )

                setattr(obj, key, value)

            obj.save(update_fields=partial.keys())
            return Sr(obj).data

        except Exception as e:
            _e404 = type(e) == self.modelConfig.model.DoesNotExist

            raise RequestHandlingError(
                f"{self.modelConfig.name}(pk={pk}) not found"
                if _e404
                else e.args[0]
                if len(e.args) > 0
                else "Unknown error",
                errorCode=e.__class__.__name__,
                statusCode=404 if _e404 else 400,
            )

    def updateMany(self, request: Request, args: dict[str, typing.Any]):
        """args[objects] should be a list of objects.
        [{pk: str|int, set: {...}}]
        """
        objects: list[PartialUpdateTyping] = args["objects"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)

        _, updatePermission = typing.cast(
            tuple[ModelPermissionTyping, UpdatePermissionTyping],
            ModelIntent.getPermission(
                role,
                "update",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            ),
        )
        checkDefault = lambda req, partialUpdate: True
        updatePermission.setdefault("check", checkDefault)

        if not all(
            [
                updatePermission.get("check", checkDefault)(request, partialUpdate)
                for partialUpdate in objects
            ]
        ):
            raise PermissionError("Unauthorized mutation", 401)

        Sr = self.modelConfig.createSerializerClass(role)

        models = (
            self.modelConfig.model.objects.all()
            if updatePermission["row"] == CellFlags.ALL
            else self.modelConfig.model.objects.filter(updatePermission["row"])
        )

        res = []  # result

        fields = (
            [
                field.name
                for field in self.modelConfig.model._meta.get_fields()
                if isinstance(field, Field)
            ]
            + [fk for fk in self.modelConfig.foreignKeys.keys()]
            if updatePermission["column"] == CellFlags.ALL
            else updatePermission["column"]
        )

        try:
            with transaction.atomic():
                for unit in objects:
                    pk = unit["pk"]  # required
                    partialUpdate = unit["partial"]  # required

                    obj: Model = models.get(pk=pk)

                    # check if user only included permitted colums in obj

                    for key, value in partialUpdate.items():
                        if not (key in fields):
                            raise RequestHandlingError(
                                f'cannot update "{key}" in {self.modelConfig.name}',
                                errorCode="",
                                statusCode=400,
                            )

                        setattr(obj, key, value)

                    obj.save(update_fields=partialUpdate.keys())
                    res.append(obj)

        except Exception as e:
            raise RequestHandlingError(
                e.args[0] if len(e.args) > 0 else "Unknown error",
                errorCode=e.__class__.__name__,
                statusCode=404
                if type(e) == self.modelConfig.model.DoesNotExist
                else 400,
            )

        return Sr(res, many=True).data

    def delete(self, request: Request, args: dict):
        pk: types.Pk = args["pk"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        _, deletePermission = typing.cast(
            tuple[ModelPermissionTyping, DeletePermissionTyping],
            ModelIntent.getPermission(
                role,
                "delete",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            ),
        )

        models = (
            self.modelConfig.model.objects.all()
            if deletePermission["row"] == CellFlags.ALL
            else self.modelConfig.model.objects.filter(deletePermission["row"])
        )

        try:
            obj: Model = models.get(pk=pk)
            obj.delete()
            return None
        except self.modelConfig.model.DoesNotExist:
            raise RequestHandlingError(
                "", errorCode=errorConstants.OBJECT_NOT_FOUND, statusCode=404
            )

    def deleteMany(self, request: Request, args: dict):
        pks: list[types.Pk] = args["pks"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        _, deletePermission = typing.cast(
            tuple[ModelPermissionTyping, DeletePermissionTyping],
            ModelIntent.getPermission(
                role,
                "delete",
                self.modelConfig.permissions,
                ModelIntent.getUserIdFromRequest(request),
            ),
        )

        models = (
            self.modelConfig.model.objects.all()
            if deletePermission["row"] == CellFlags.ALL
            else self.modelConfig.model.objects.filter(deletePermission["row"])
        )

        try:
            with transaction.atomic():
                instances: list[Model] = [models.get(pk=pk) for pk in pks]
                for instance in instances:
                    instance.delete()
            return None
        except self.modelConfig.model.DoesNotExist:
            raise RequestHandlingError(
                "", errorCode=errorConstants.OBJECT_NOT_FOUND, statusCode=404
            )

    @property
    def intenthandlers(self) -> dict[str, IntentFunction]:
        name = self.modelConfig.name

        rel = {
            ModelOperations.SELECT_ONE: (
                f"models.{name}.find",
                IntentFunction(self.find, requiredArgs=("where",)),
            ),
            ModelOperations.SELECT_MANY: (
                f"models.{name}.selectmany",
                IntentFunction(self.selectMany, optionalArgs=("where",)),
            ),
            ModelOperations.INSERT: (
                f"models.{name}.insert",
                IntentFunction(self.insert, requiredArgs=("object",)),
            ),
            ModelOperations.INSERT_MANY: (
                f"models.{name}.insertmany",
                IntentFunction(
                    self.insertMany,
                    requiredArgs=("objects",),
                ),
            ),
            ModelOperations.UPDATE: (
                f"models.{name}.update",
                IntentFunction(self.update, requiredArgs=("pk", "partial")),
            ),
            ModelOperations.UPDATE_MANY: (
                f"models.{name}.updatemany",
                IntentFunction(self.updateMany, requiredArgs=("objects",)),
            ),
            ModelOperations.DELETE: (
                f"models.{name}.delete",
                IntentFunction(self.delete, requiredArgs=("pk",)),
            ),
            ModelOperations.DELETE_MANY: (
                f"models.{name}.deletemany",
                IntentFunction(self.delete, requiredArgs=("pks",)),
            ),
        }

        # filter functions to publish based on configuration
        for i in [*rel.keys()]:
            if not (i in self.modelConfig.allowedOperations):
                del rel[i]

        return dict([pair for pair in rel.values()])

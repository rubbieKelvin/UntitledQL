from uql.model import ModelConfig
from uql.config import UQLConfig
from uql.constants import CellFlags
from uql.constants import ModelOperations
from uql.utils import templates as t
from uql.utils.query import makeQuery
from uql.utils.exceptions import Interruption

from rest_framework.request import Request

from django.db import transaction
from django.db.models import Field, Model
from django.db.utils import IntegrityError

from . import IntentFunction


class ModelIntent:
    def __init__(self, rootConfig: UQLConfig, modelConfig: ModelConfig) -> None:
        self.modelConfig = modelConfig
        self.rootConfig = rootConfig

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

        # get permission config
        # pass the user id here since we're trying to get the rows
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        try:
            Sr = self.modelConfig.createSerializerClass(role)
        except PermissionError as e:
            raise Interruption(
                t.error(
                    message=str(e),
                    type="PERMISSION_ERROR",
                    code=401,
                )
            )

        query = makeQuery(where) if where else None
        models = (
            self.modelConfig.model.objects.all()
            if permission.select.row == True
            else self.modelConfig.model.objects.filter(permission.select.row)
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

        # get permission config
        # pass the user id here since we're trying to get the rows
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        try:
            Sr = self.modelConfig.createSerializerClass(role)
        except PermissionError as e:
            raise Interruption(
                t.error(
                    message=str(e),
                    type="PERMISSION_ERROR",
                    code=401,
                )
            )

        query = makeQuery(where) if where else None
        models = (
            self.modelConfig.model.objects.all()
            if permission.select.row == True
            else self.modelConfig.model.objects.filter(permission.select.row)
        )
        models = models.filter(query) if query else models
        return Sr(models, many=True).data

    def insert(self, request: Request, args: dict):
        obj: dict = args["object"]  # required

        # get role and permission config
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        # check permission's there
        # check insert's there
        # check that the obj values is valid

        _pass_check = False
        _has_insert_permission = permission and permission.insert

        if _has_insert_permission:
            _pass_check = obj and permission.insert.check(request, obj)

        if not (_has_insert_permission and _pass_check):
            raise Interruption(
                t.error(
                    message=(
                        "Unauthorized mutation"
                        if not _pass_check
                        else f'User with role "{role}" cannot insert into {self.modelConfig.name}'
                    ),
                    type="PERMISSION_ERROR",
                    code=401,
                )
            )

        # required fields should be a subset of insertable column
        if not set(permission.insert.requiredFields).issubset(permission.insert.column):
            raise Exception(
                "insert.requiredFields should be a subset of insert.columns"
            )

        # check if required field's in obj
        if not set(permission.insert.requiredFields).issubset(obj.keys()):
            raise Exception(
                f"requires fields ({', '.join(permission.insert.requiredFields)})"
            )

        # check if user only included permitted colums in obj
        fields = (
            [
                field.name
                for field in self.modelConfig.model._meta.get_fields()
                if isinstance(field, Field)
            ]
            + [fk for fk in self.modelConfig.foreignKeys.keys()]
            if permission.insert.column == CellFlags.ALL_COLUMNS
            else permission.insert.column
        )

        for key in obj.keys():
            if not (key in fields):
                raise Interruption(
                    t.error(
                        message=f'cannot insert "{key}" in {self.modelConfig.name}',
                        type="UNKNOWN_KEYS",
                        code=400,
                    )
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
                obj[key] = fk.getObject(obj[key])

        try:
            # create model
            model = self.modelConfig.model(**obj)
            model.save()

            # get model data from select realizers
            Sr = self.modelConfig.createSerializerClass(role)
            return Sr(model).data

        except Exception as e:
            raise Interruption(
                t.error(
                    message=str(e),
                    type=e.__class__.__name__ or "UNKNOWN_ERROR",
                    code=400,
                )
            )

    def insertMany(self, request: Request, args: dict):
        objects: list[dict] = args["objects"]  # required

        # get role and permission config
        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        # check permission's there
        # check insert's there
        # check that the _set values is valid

        _pass_check = False
        _has_insert_permission = permission and permission.insert

        if _has_insert_permission:
            _pass_check = objects and all(
                [permission.insert.check(request, obj) for obj in objects]
            )

        if not (_has_insert_permission and _pass_check):
            raise Interruption(
                t.error(
                    message=(
                        "Unauthorized mutation"
                        if not _pass_check
                        else f'User with role "{role}" cannot insert into {self.modelConfig.name}'
                    ),
                    type="PERMISSION_ERROR",
                    code=401,
                )
            )

        # get model data from select realizers
        Sr = self.modelConfig.createSerializerClass(role)

        # required fields should be a subset of insertable column
        if not set(permission.insert.requiredFields).issubset(permission.insert.column):
            raise Exception(
                "insert.requiredFields should be a subset of insert.columns"
            )

        # check if required field's in each object
        if not all(
            [
                set(permission.insert.requiredFields).issubset(obj.keys())
                for obj in objects
            ]
        ):
            raise Exception(
                f"requires fields ({', '.join(permission.insert.requiredFields)})"
            )

        # check if user only included permitted colums in each object
        fields = (
            [
                field.name
                for field in self.modelConfig.model._meta.get_fields()
                if isinstance(field, Field)
            ]
            + [fk for fk in self.modelConfig.foreignKeys.keys()]
            if permission.insert.column == CellFlags.ALL_COLUMNS
            else permission.insert.column
        )

        res = []  # result

        try:
            with transaction.atomic():
                for obj in objects:
                    for key in obj.keys():
                        if not (key in fields):
                            raise Interruption(
                                t.error(
                                    message=f'cannot insert "{key}" in {self.modelConfig.name}',
                                    type="UNKNOWN_KEYS",
                                    code=400,
                                )
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
                            obj[key] = fk.getObject(obj[key])

                    # create model
                    model = self.modelConfig.model(**obj)
                    model.save()

                    res.append(model)

        except (transaction.TransactionManagementError, IntegrityError) as e:
            raise Interruption(
                t.error(
                    message=str(e),
                    type=e.__class__.__name__ or "DATABASE_ERROR",
                    code=400,
                )
            )

        return Sr(res, many=True).data

    def update(self, request: Request, args: dict):
        _set: dict = args["set"]  # required
        pk: int | str = args["pk"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        if not (
            role
            and permission
            and permission.update
            and permission.update.check(request, {"pk": pk, "set": _set})
        ):
            raise Interruption(t.error(message="", type="PERMISSION_ERROR", code=401))

        Sr = self.modelConfig.createSerializerClass(role)

        models = (
            self.modelConfig.model.objects.all()
            if permission.update.row == True
            else self.modelConfig.model.objects.filter(permission.update.row)
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
                if permission.update.column == CellFlags.ALL_COLUMNS
                else permission.update.column
            )

            for key, value in _set.items():
                if not (key in fields):
                    raise Interruption(
                        t.error(
                            message=f'cannot update "{key}" in {self.modelConfig.name}',
                            type="UNKNOWN_KEYS",
                            code=400,
                        )
                    )

                setattr(obj, key, value)

            obj.save(update_fields=_set.keys())
            return Sr(obj).data

        except (self.modelConfig.model.DoesNotExist, IntegrityError) as e:
            e404 = type(e) == self.modelConfig.model.DoesNotExist
            raise Interruption(
                t.error(
                    message=f"{self.modelConfig.name}(pk={pk}) not found"
                    if e404
                    else str(e),
                    type="OBJECT_NOT_FOUND" if e404 else e.__class__.__name__,
                    code=404 if e404 else 400,
                )
            )

    def updateMany(self, request: Request, args: dict):
        """args[objects] should be a list of objects.
        [{pk: str|int, set: {...}}]
        """
        objects = args["objects"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        if not (
            role
            and permission
            and permission.update
            and all([permission.update.check(request, obj) for obj in objects])
        ):
            raise Interruption(t.error(message="", type="PERMISSION_ERROR", code=401))

        Sr = self.modelConfig.createSerializerClass(role)

        models = (
            self.modelConfig.model.objects.all()
            if permission.update.row == True
            else self.modelConfig.model.objects.filter(permission.update.row)
        )

        res = []  # result

        fields = (
            [
                field.name
                for field in self.modelConfig.model._meta.get_fields()
                if isinstance(field, Field)
            ]
            + [fk for fk in self.modelConfig.foreignKeys.keys()]
            if permission.update.column == CellFlags.ALL_COLUMNS
            else permission.update.column
        )

        try:
            with transaction.atomic():
                for obj in objects:
                    pk = obj["pk"]  # required
                    _set = obj["set"]  # required

                    obj: Model = models.get(pk=pk)

                    # check if user only included permitted colums in obj

                    for key, value in _set.items():
                        if not (key in fields):
                            raise Interruption(
                                t.error(
                                    message=f'cannot update "{key}" in {self.modelConfig.name}',
                                    type="UNKNOWN_KEYS",
                                    code=400,
                                )
                            )

                        setattr(obj, key, value)

                    obj.save(update_fields=_set.keys())
                    res.append(obj)

        except (self.modelConfig.model.DoesNotExist, IntegrityError) as e:
            e404 = type(e) == self.modelConfig.model.DoesNotExist
            raise Interruption(
                t.error(
                    message=f"{self.modelConfig.name}(pk={pk}) not found"
                    if e404
                    else str(e),
                    type="OBJECT_NOT_FOUND" if e404 else e.__class__.__name__,
                    code=404 if e404 else 400,
                )
            )

        return Sr(res, many=True).data

    def delete(self, request: Request, args: dict):
        pk = args["pk"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        if not (role and permission and permission.delete):
            raise Interruption(t.error(message="", type="PERMISSION_ERROR", code=401))

        Sr = self.modelConfig.createSerializerClass(role)

        models = (
            self.modelConfig.model.objects.all()
            if permission.delete.row == True
            else self.modelConfig.model.objects.filter(permission.delete.row)
        )

        try:
            obj: Model = models.get(pk=pk)
            res = Sr(obj).data
            obj.delete()
            return res
        except self.modelConfig.model.DoesNotExist:
            raise Interruption(t.error(message="", type="OBJECT_NOT_FOUND", code=404))

    def deleteMany(self, request: Request, args: dict):
        pks = args["pks"]  # required

        role = self.rootConfig.getAuthenticatedUserRoles(request.user)
        permission = self.modelConfig.permissions.get(role, lambda x: None)(
            getattr(request.user, "id", None)
        )

        if not (role and permission and permission.delete):
            raise Interruption(t.error(message="", type="PERMISSION_ERROR", code=401))

        Sr = self.modelConfig.createSerializerClass(role)

        models = (
            self.modelConfig.model.objects.all()
            if permission.delete.row == True
            else self.modelConfig.model.objects.filter(permission.delete.row)
        )

        try:
            objects: Model = [models.get(pk=pk) for pk in pks]
            res = Sr(objects, many=True).data
            [obj.delete() for obj in objects]
            return res
        except self.modelConfig.model.DoesNotExist:
            raise Interruption(t.error(message="", type="OBJECT_NOT_FOUND", code=404))

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
                IntentFunction(self.update, requiredArgs=("pk", "set")),
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

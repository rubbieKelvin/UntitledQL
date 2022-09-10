from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from django.http.response import HttpResponseBase
from django.db.models import Model, Q

from . import templates
from .model import ModelConfig
from .utils import fromDotNotation, selectKeys
from .exceptions import UnrestError
from .query import mapQ
from .handlers import IntentHandler

from dataclasses import dataclass
from typing import Callable, Any


class UnrestAdapterBaseConfig:
    raise_exceptions = False  # raise exception if an error occurs in intent handler
    models: list[ModelConfig] = []  # model configurations for unrest
    functions: list[IntentHandler] = []  # functions config for unrest

    @staticmethod
    def getAuthenticatedUserRoles(user: Model) -> str:
        """the calling function to get the role for a user"""
        raise NotImplementedError


def createUnrestAdapter(config: type[UnrestAdapterBaseConfig]) -> HttpResponseBase:
    def response_decorator(fn):
        def _(*args, **kwargs):

            try:
                res = fn(*args, **kwargs)
                if not res:
                    raise ValueError("intent did not return any data")
            except Exception as e:
                if config.raise_exceptions:
                    raise e
                res = templates.response(
                    error=templates.Error(
                        message=str(e), type="INTERNAL_SERVER_ERROR", code=500
                    )
                )

            return Response(res, status=res["meta"]["status_code"])

        return _

    # this is the root for all intents
    root = {"models": {}}

    # load up model functions
    for modelConfig in config.models:

        def select(request, args):
            role = config.getAuthenticatedUserRoles(request.user)

            permission = modelConfig.permissions.get(role, None)

            if not permission or not permission.select and permission.select.row:
                raise UnrestError(
                    templates.Error(
                        message=f'user with role "{role}" cannot access this data',
                        type="PERMISSION_ERROR",
                        code=401,
                    )
                )

            query = mapQ(args["where"])

            res = (
                modelConfig.model.objects.all()
                if permission.select.row == True
                else modelConfig.model.objects.filter(permission.select.row)
            ).filter(query or Q())

            class Sr(ModelSerializer):
                class Meta:
                    model = modelConfig.model
                    fields = permission.select.column

            return Sr(res, many=True).data

        def insert(request, args):
            pass

        def insert_many(request, args):
            pass

        def update(request, args):
            pass

        def update_many(request, args):
            pass

        def delete(request, args):
            pass

        def delete_many(request, args):
            pass

        root["models"][modelConfig.name] = {
            "select": IntentHandler(
                select, optionalArgs=("where",), defaultValues={"where": {}}
            ),
            "insert": IntentHandler(insert),
            "insert_many": IntentHandler(insert_many),
            "update": IntentHandler(update),
            "update_many": IntentHandler(update_many),
            "delete": IntentHandler(delete),
            "delete_many": IntentHandler(delete_many),
        }

    # ...
    class UnrestAdapter(APIView):
        @response_decorator
        def post(self, request: Request) -> Response:
            # get response data
            body = request.data

            # tells the app what function to call
            intent = body.get("intent")

            # specifies the return type of the function;
            # should only be used on dicts or lists of dicts
            fields = body.get("fields", {})

            # arguments are values to be passed into the handler function
            # there are required and optional arguments, so the keys in this data should meet the requirements
            arguments = body.get("args", {})

            # intents are required to use this app
            if intent == None:
                return templates.response(
                    data=None,
                    error=templates.Error(
                        message="intent not provided", type="NO_INTENT"
                    ),
                )

            # get the function that handles from root
            handler: IntentHandler = fromDotNotation(root, intent)
            warning = (
                "fields not specified, you might get an empty data"
                if not fields
                else None
            )

            try:
                data = handler(request, arguments)

                # raise an error if the intent handler returned any thing other than
                # the instances of dict or list or tuple
                if not (
                    isinstance(data, dict) or hasattr(data, "__iter__") or data == None
                ):
                    raise UnrestError(
                        templates.Error(message="intent should return a list or object")
                    )

                # if there's no data, do not filter response
                if data != None:
                    if hasattr(data, "__iter__"):
                        copy = [*data]
                        [selectKeys(i, fields) for i in copy]
                    else:
                        copy = {**data}
                        selectKeys(copy, fields)
                else:
                    copy = data

                # return
                return templates.response(data=copy, warning=warning)

            except Exception as e:

                # catch all exceptions and return them as error response
                if config.raise_exceptions:
                    raise e

                return templates.response(
                    error=e.errortemplate
                    if type(e) == UnrestError
                    else templates.Error(
                        message=f'error running "{intent}": {e}',
                        code=400,
                    )
                )

    return UnrestAdapter.as_view()

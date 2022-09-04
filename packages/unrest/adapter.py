from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from django.http.response import HttpResponseBase
from django.db.models import Model

from . import templates
from .model import ModelConfig
from .utils import fromDotNotation
from .exceptions import UnrestError

from dataclasses import dataclass
from typing import Callable, Any


def intenthandler(
    optional_args: set[str] = None,
    required_args: set[str] = None,
    default_values: dict[str, Any] = None,
    allow_unknow_arguments: bool = False,
):
    # ...
    required_args = required_args or set()
    optional_args = optional_args or set()
    default_values = default_values or {}
    all_args = optional_args.union(required_args)

    def decorator(function: Callable[[Request, dict[str, Any]], Any]):
        def _(request: Request, options: dict[str, Any]):

            # check if required args are present
            if not (required_args.issubset(options.keys())):
                raise UnrestError(
                    templates.Error(
                        message=f'required keys "{required_args.difference(options.keys())}" not given in argument',
                        code=400,
                        type="MISSING_REQUIRED_ARGS",
                    )
                )

            # if required args have default argument, raise an error
            if default_values and set(default_values.keys()).issubset(required_args):
                raise UnrestError(
                    templates.Error(
                        message="required arguments should not have default values",
                        code=400,
                        type="DEFAULT_ON_REQUIRED_ARGS",
                    )
                )

            # if we do mind foriegn args, check if all arg in oprions was specified
            if not allow_unknow_arguments and not set(options.keys()).issubset(
                all_args
            ):
                raise UnrestError(
                    templates.Error(
                        message=f'unknown keys "{set(options.keys()).difference(all_args)}"',
                        code=400,
                        type="UNKNOWN_ARGS",
                    )
                )

            for key, val in default_values.items():
                options.setdefault(key, val)

            return function(request, options)

        return _

    return decorator


class UnrestAdapterBaseConfig:
    raise_exceptions = False
    models: list[ModelConfig] = []
    functions = []

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

    root = {"models": {}}

    # load up model functions
    for modelConfig in config.models:

        @intenthandler(optional_args={"query"}, default_values={"query": {}})
        def select(request, options):
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

            res = (
                modelConfig.model.objects.all()
                if permission.select.row == True
                else modelConfig.model.objects.filter(permission.select.row)
            )

            class Sr(ModelSerializer):
                class Meta:
                    model = modelConfig.model
                    fields = permission.select.column

            return Sr(res, many=True).data

        @intenthandler()
        def insert(request, options):
            pass

        @intenthandler()
        def insert_many(request, options):
            pass

        @intenthandler()
        def update(request, options):
            pass

        @intenthandler()
        def update_many(request, options):
            pass

        @intenthandler()
        def delete(request, options):
            pass

        @intenthandler()
        def delete_many(request, options):
            pass

        root["models"][modelConfig.name] = {
            "select": select,
            "insert": insert,
            "insert_many": insert_many,
            "update": update,
            "update_many": update_many,
            "delete": delete,
            "delete_many": delete_many,
        }

    # ...
    class UnrestAdapter(APIView):
        @response_decorator
        def post(self, request: Request) -> Response:
            body = request.data
            intent = body.get("intent")
            arguments = body.get("arguments", {})

            if intent == None:
                return templates.response(
                    data=None,
                    error=templates.Error(
                        message="intent not provided", type="NO_INTENT"
                    ),
                )

            handler: Callable = fromDotNotation(root, intent)

            try:
                return templates.response(data=handler(request, arguments))
            except Exception as e:
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

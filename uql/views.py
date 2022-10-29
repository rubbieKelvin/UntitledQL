from .config import UQLConfig
from .intent.model import ModelIntent
from .intent import IntentFunction
from .utils import templates as t
from .utils.select import selectKeys
from .utils.types import isArray
from .utils.types import isMap
from .exceptions import RequestHandlingError
from .constants import errors as errorConstants

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

import typing
from typing_extensions import NotRequired


class UQLRequestBodyTyping(typing.TypedDict):
    """Base structure for uql request input"""

    intent: str | None
    fields: bool | dict | None
    args: dict[str, typing.Any]


class UQLResponseMetaTyping(typing.TypedDict):
    hasError: bool


class UQLResponseBodyTyping(typing.TypedDict):
    data: typing.Mapping | typing.Sequence | None
    error: t.ErrorTyping | None
    warning: NotRequired[str | None]
    statusCode: int
    meta: UQLResponseMetaTyping


def UQLView(config: type[UQLConfig]) -> type[APIView]:
    """Creates an APIView class that is built on config.

    Args:
        config (type[UQLConfig]): _description_

    Returns:
        type[APIView]: _description_
    """

    def rootErrorHandler(fn):
        """
        Decorates the response to handle all errors from view.
        """

        def _(*args, **kwargs) -> Response:

            try:
                res: UQLResponseBodyTyping = fn(*args, **kwargs)

            except Exception as e:
                if config.raise_exceptions:
                    # raise error as per stated in app's configuration
                    raise e

                if type(e) == RequestHandlingError:
                    e = typing.cast(RequestHandlingError, e)
                    return Response(
                        t.error(
                            e.message,
                            errorCode=e.errorCode,
                            statusCode=e.statusCode,
                            summary=e.summary,
                        ),
                        status=e.statusCode,
                    )
                else:
                    return Response(
                        t.error(
                            e.args[0] if len(e.args) > 0 else e.__class__.__name__,
                            errorCode=e.__class__.__name__,
                            statusCode=e.args[1] if len(e.args) > 1 else 500,
                        )
                    )

            if type(res) == list:
                return Response(res, status=200)

            # TODO: review res
            return Response(res, status=res["statusCode"])

        return _

    # this is the root for intents
    modelRoots = {}
    functionRoots = {}

    # load up func roots
    for wrapper in config.functions:
        functionRoots[f"functions.{wrapper.name}"] = wrapper

    # load up model roots
    for modelConfig in config.models:
        modelRoots.update(ModelIntent(config, modelConfig).intenthandlers)

    class Adapter(APIView):
        ROOT: dict[str, IntentFunction] = {**modelRoots, **functionRoots}

        def handleIntent(
            self,
            request: Request,
            intent: str | None,
            fields: bool | dict | None,
            arguments: dict[str, typing.Any],
        ) -> UQLResponseBodyTyping:
            # intents are required to use this app
            if intent == None:
                raise RequestHandlingError(
                    "No specified intent",
                    errorCode=errorConstants.NO_INTENT,
                    statusCode=400,
                    summary="Could not find any specified intent during request call",
                )

            if not (intent in self.ROOT):
                raise RequestHandlingError(
                    "Intent does not exist",
                    errorCode=errorConstants.INEXISTENT_INTENT,
                    statusCode=400,
                    summary=f'Intent "{intent}" does not exist in uql root.\nThis is a development error, refer to schema to see available intents.',
                )

            # get the function that would handles current request from root
            handler: IntentFunction = self.ROOT[intent]

            warning = (
                "fields not specified, you might get an empty data"
                if fields == None
                else None
            )

            data = handler(request, arguments)

            # raise an error if the intent handler returned any thing other than
            # the instances of dict or list or tuple or none
            if not (data == None or isMap(data) or isArray(data)):
                raise RequestHandlingError(
                    "Invalid handler output",
                    errorCode=errorConstants.INVALID_REQUEST_HANDLER_OUTPUT,
                    statusCode=500,
                    summary=f"Intent ({intent}) handler returned a {type(data)} type. allowed output types are dict, list, none",
                )

            # if there's no data, do not filter response
            if data == None:
                return {
                    "data": None,
                    "error": None,
                    "warning": warning,
                    "statusCode": 200,
                    "meta": {"hasError": False},
                }

            # psuedo data function
            _data = lambda: data

            if isMap(data):
                _data = lambda: selectKeys(
                    typing.cast(dict, data), typing.cast(dict, fields)
                )
            else:
                _data = lambda: [
                    selectKeys(i, typing.cast(dict, fields)) if isMap(i) else i
                    for i in typing.cast(typing.Sequence[typing.Any], data)
                ]

            # check fields to compute result
            if fields:
                if type(fields) == dict:
                    result = _data()
                else:
                    result = data
            else:
                result = None

            # return result
            return {
                "data": result,
                "warning": warning,
                "statusCode": 200,
                "error": None,
                "meta": {"hasError": False},
            }

        def get(self, request: Request) -> Response:
            if config.show_docs:
                root = self.ROOT
                result = {key: {**val.json(), "name": key} for key, val in root.items()}
                return Response(result)
            return Response(data={"msg": 'set "show_docs" to True in uql config'})

        @rootErrorHandler
        def post(
            self, request: Request
        ) -> UQLResponseBodyTyping | list[UQLResponseBodyTyping]:
            # get response data
            body = request.data

            if type(body) == dict:
                body = typing.cast(UQLRequestBodyTyping, body)
                body.setdefault("intent", None)
                body.setdefault("fields", None)
                body.setdefault("args", {})

                # tells the app what function to call
                intent = body["intent"]

                # specifies the return type of the function;
                # should only be used on dicts or lists of dicts
                # -- bool   : include all fields or not
                # -- dict   : include selected fields
                # -- None   : no fields
                fields = body["fields"]

                # arguments are values to be passed into the handler function
                # there are required and optional arguments, so the keys in this data should meet the requirements
                arguments = body["args"]

                return self.handleIntent(request, intent, fields, arguments)

            elif type(body) == list:

                # sequentially run multiple intent in on call
                body = typing.cast(list[UQLRequestBodyTyping], body)
                responseData: list[UQLResponseBodyTyping] = []

                for cell in body:
                    cell.setdefault("intent", None)
                    cell.setdefault("fields", None)
                    cell.setdefault("args", {})

                    responseData.append(
                        self.handleIntent(
                            request, cell["intent"], cell["fields"], cell["args"]
                        )
                    )
                return responseData
            else:
                raise RequestHandlingError(
                    f"Unknown body type: {type(body)}",
                    statusCode=400,
                    errorCode=errorConstants.INVALID_REQUEST_BODY,
                )

    return Adapter

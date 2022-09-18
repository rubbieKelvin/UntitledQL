from .config import UQLConfig
from .intent import ModelIntent
from .intent import IntentModule
from .intent import IntentFunction
from .utils import templates as t
from .utils.select import selectKeys
from .utils.exceptions import Interruption
from .utils.types import isArray
from .utils.types import isMap

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from collections.abc import Mapping
from collections.abc import Sequence


def UQLView(config: type[UQLConfig]) -> type[APIView]:
    """Creates an APIView class that is built on config.

    Args:
        config (type[UQLConfig]): _description_

    Returns:
        type[APIView]: _description_
    """

    def response_decorator(fn):
        """Decorates the response to handle all errors from view"""

        def _(*args, **kwargs):

            try:
                res = fn(*args, **kwargs)
                if not res:
                    raise ValueError("intent did not return any data")

            except Exception as e:
                if config.raise_exceptions:
                    raise e

                res = t.response(
                    error=t.error(
                        code=500,
                        message=str(e),
                        type="INTERNAL_SERVER_ERROR",
                    )
                )

            return Response(res, status=res["meta"]["status_code"])

        return _

    # this is the root for intents
    modelRoots = {}
    functionRoots = {}

    # load up func roots
    for wrapper in config.functions:
        if type(wrapper) == IntentModule:
            functionRoots.update(
                {f"functions.{k}": v for k, v in wrapper.spread.items()}
            )
        elif type(wrapper) == IntentFunction:
            functionRoots[f"functions.{wrapper.name}"] = wrapper

    # load up model roots
    for modelConfig in config.models:
        modelRoots.update(ModelIntent(config, modelConfig).intenthandlers)

    class Adapter(APIView):
        ROOT = {**modelRoots, **functionRoots}

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
                return t.response(
                    data=None,
                    error=t.error(message="intent not provided", type="NO_INTENT"),
                )

            # get the function that handles from root
            handler: IntentFunction = self.ROOT[intent]

            warning = (
                "fields not specified, you might get an empty data"
                if not fields
                else None
            )

            try:
                data = handler(request, arguments)

                # raise an error if the intent handler returned any thing other than
                # the instances of dict or list or tuple
                if not (data == None or isMap(data) or isArray(data)):
                    raise Interruption(
                        t.error(message="intent should return a array or map, none")
                    )

                # if there's no data, do not filter response
                if data != None:
                    if isMap(data):
                        return t.response(
                            data=selectKeys(data, fields), warning=warning
                        )

                    elif isArray(data):
                        return t.response(
                            data=[selectKeys(i, fields) for i in data], warning=warning
                        )

                # return
                return t.response(data=None, warning=warning)

            except Exception as e:

                # catch all exceptions and return them as error response
                if config.raise_exceptions:
                    raise e

                return t.response(
                    error=e.errortemplate
                    if type(e) == Interruption
                    else t.error(
                        message=f'error running "{intent}": {e}',
                        code=400,
                    )
                )

    return Adapter

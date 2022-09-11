from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from django.http.response import HttpResponseBase

from . import templates
from .utils import selectKeys
from .exceptions import UnrestError
from .handlers import IntentHandler, ModelIntentHandler
from .config import UnrestAdapterBaseConfig


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

    # this is the root for intents
    modelRoots = {}
    functionRoots = {}

    # load up func roots
    functionRoots = {
        f"functions.{intentWrapper.name}": intentWrapper
        for intentWrapper in config.functions
    }

    # load up model roots
    for modelConfig in config.models:
        modelRoots.update(ModelIntentHandler(config, modelConfig).intenthandlers)

    class UnrestAdapter(APIView):
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
                return templates.response(
                    data=None,
                    error=templates.Error(
                        message="intent not provided", type="NO_INTENT"
                    ),
                )

            # get the function that handles from root
            handler: IntentHandler = self.ROOT[intent]

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

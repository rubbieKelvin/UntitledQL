from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from django.http.response import HttpResponseBase
from django.db.models import Model

class UnrestAdapterBaseConfig():
    models = []
    functions = []

    def getAuthenticatedUserRoles(user:Model) -> list[str]:
        """the calling function to get the list of roles for a user"""
        raise NotImplementedError

def createUnrestAdapter(config: type[UnrestAdapterBaseConfig]) -> HttpResponseBase:
    # ...
    class UnrestAdapter(APIView):
        def get(self, request: Request) -> Response:
            return Response()
    
    return UnrestAdapter.as_view()
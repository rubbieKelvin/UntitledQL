from django.contrib import admin
from django.urls import path
from uql.views import UQLView

from .config import Config

urlpatterns = [
    path("admin/", admin.site.urls),
    path("uql/", UQLView(Config).as_view())
]

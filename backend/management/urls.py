from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def home(request):
    return HttpResponse("Welcome to the Stock Management API")


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

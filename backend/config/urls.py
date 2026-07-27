from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("common.urls")),
    path("api/v1/", include("cases.urls")),
    path("api/v1/", include("predictions.urls")),
]

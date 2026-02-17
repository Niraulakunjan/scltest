from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("site-admin/", admin.site.urls),
    path("", include("portal.urls")),
]

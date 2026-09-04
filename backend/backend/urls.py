"""URL routes for the Wonder Painter backend."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from painter import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("csrf/", views.csrf_token),
    path("register/", views.register),
    path("resend-verification/", views.resend_verification),
    path("login/", views.login),
    path("logout/", views.logout),
    path("session/", views.session_status),
    path("validate/", views.validate),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

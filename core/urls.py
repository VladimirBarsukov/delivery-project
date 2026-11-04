from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(
        template_name="waybills/login.html"
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(
        next_page="/login/"
    ), name="logout"),
    path("api/waybills/", include("waybills.urls")),
    path("", include("waybills.urls")),
]
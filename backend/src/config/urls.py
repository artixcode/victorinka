from django.contrib import admin
from django.urls import path
from apps.core import views as core_views
from apps.users.views import RegisterView, LoginView, MeView, LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.home, name="home"),
    path("health/", core_views.health, name="health"),

    # Auth API
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
]

from django.contrib import admin
from django.urls import path
from apps.core import views as core_views
from apps.users.views import RegisterView, LoginView, MeView, LogoutView
from apps.rooms.views import MyRoomsListView, RoomCreateView, RoomDetailView, RoomJoinView, RoomLeaveView
from apps.questions.views import MyQuestionsListCreateView, MyQuestionDetailView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.home, name="home"),
    path("health/", core_views.health, name="health"),

    # Auth API
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),

    # Rooms
    path("api/rooms/mine/", MyRoomsListView.as_view()),
    path("api/rooms/", RoomCreateView.as_view()),
    path("api/rooms/<int:pk>/", RoomDetailView.as_view()),
    path("api/rooms/<int:pk>/join/", RoomJoinView.as_view()),
    path("api/rooms/<int:pk>/leave/", RoomLeaveView.as_view()),

    #questions
    path("api/questions/", MyQuestionsListCreateView.as_view()),
    path("api/questions/<int:pk>/", MyQuestionDetailView.as_view()),
]

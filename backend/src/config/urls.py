from django.contrib import admin
from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from apps.core import views as core_views
from apps.users.views import RegisterView, LoginView, MeView, LogoutView, LogoutAllView
from apps.rooms.views import MyRoomsListView, RoomCreateView, RoomDetailView, RoomJoinView, RoomLeaveView
from apps.questions.views import (
    MyQuestionsListCreateView,
    MyQuestionDetailView,
    MyQuizzesListCreateView,
    MyQuizDetailView,
    PublicQuizzesListView,
    PublicQuizDetailView,
    TopicListView,
    TagListView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Victorina API",
        default_version="v1",
        description="API документация",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.home, name="home"),
    path("health/", core_views.health, name="health"),

    #swagger
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),

    # Auth API
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/auth/logout_all/", LogoutAllView.as_view(), name="logout_all"),

    # Rooms
    path("api/rooms/mine/", MyRoomsListView.as_view()),
    path("api/rooms/", RoomCreateView.as_view()),
    path("api/rooms/<int:pk>/", RoomDetailView.as_view()),
    path("api/rooms/<int:pk>/join/", RoomJoinView.as_view()),
    path("api/rooms/<int:pk>/leave/", RoomLeaveView.as_view()),

    # Topics & Tags
    path("api/topics/", TopicListView.as_view(), name="topics-list"),
    path("api/tags/", TagListView.as_view(), name="tags-list"),

    # Questions
    path("api/questions/", MyQuestionsListCreateView.as_view(), name="my-questions"),
    path("api/questions/<int:pk>/", MyQuestionDetailView.as_view(), name="my-question-detail"),

    # Quizzes (Мои)
    path("api/quizzes/mine/", MyQuizzesListCreateView.as_view(), name="my-quizzes"),
    path("api/quizzes/mine/<int:pk>/", MyQuizDetailView.as_view(), name="my-quiz-detail"),

    # Quizzes (Публичные - каталог)
    path("api/quizzes/", PublicQuizzesListView.as_view(), name="public-quizzes"),
    path("api/quizzes/<int:pk>/", PublicQuizDetailView.as_view(), name="public-quiz-detail"),
]

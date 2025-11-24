from django.contrib import admin
from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.conf import settings
from apps.core import views as core_views
from apps.users.views import (
    RegisterView, LoginView, MeView, LogoutView, LogoutAllView,
    MyBookmarksListView, BookmarkCreateView, BookmarkDetailView,
    MyGameHistoryView, MyActiveRoomsView, MyStatsView,
    PasswordResetRequestView, PasswordResetConfirmView, PasswordResetTokenListView
)
from apps.users.leaderboard_views import (
    GlobalLeaderboardView, QuizLeaderboardView, RoomLeaderboardView, UserStatsDetailView
)
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
    HomePageView,
)
from apps.game import views as game_views

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
    path("ws-test/", core_views.websocket_test, name="websocket-test"),  # Тестовая страница WebSocket

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

    # Password Reset (восстановление пароля)
    path("api/auth/password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("api/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("api/auth/password-reset/tokens/", PasswordResetTokenListView.as_view(), name="password-reset-tokens"),

    # Rooms
    path("api/rooms/mine/", MyRoomsListView.as_view()),
    path("api/rooms/", RoomCreateView.as_view()),
    path("api/rooms/<int:pk>/", RoomDetailView.as_view()),
    path("api/rooms/<int:pk>/join/", RoomJoinView.as_view()),
    path("api/rooms/<int:pk>/leave/", RoomLeaveView.as_view()),

    # Topics & Tags
    path("api/topics/", TopicListView.as_view(), name="topics-list"),
    path("api/tags/", TagListView.as_view(), name="tags-list"),

    # Home page (популярные викторины)
    path("api/home/", HomePageView.as_view(), name="home-page"),

    # Questions
    path("api/questions/", MyQuestionsListCreateView.as_view(), name="my-questions"),
    path("api/questions/<int:pk>/", MyQuestionDetailView.as_view(), name="my-question-detail"),

    # Quizzes (Мои)
    path("api/quizzes/mine/", MyQuizzesListCreateView.as_view(), name="my-quizzes"),
    path("api/quizzes/mine/<int:pk>/", MyQuizDetailView.as_view(), name="my-quiz-detail"),

    # Quizzes (Публичные - каталог)
    path("api/quizzes/", PublicQuizzesListView.as_view(), name="public-quizzes"),
    path("api/quizzes/<int:pk>/", PublicQuizDetailView.as_view(), name="public-quiz-detail"),

    # Личный кабинет
    # Закладки
    path("api/cabinet/bookmarks/", MyBookmarksListView.as_view(), name="my-bookmarks"),
    path("api/cabinet/bookmarks/add/", BookmarkCreateView.as_view(), name="bookmark-add"),
    path("api/cabinet/bookmarks/<int:pk>/", BookmarkDetailView.as_view(), name="bookmark-detail"),

    # История игр
    path("api/cabinet/history/", MyGameHistoryView.as_view(), name="my-game-history"),

    # Активные комнаты
    path("api/cabinet/active-rooms/", MyActiveRoomsView.as_view(), name="my-active-rooms"),

    # Статистика
    path("api/cabinet/stats/", MyStatsView.as_view(), name="my-stats"),

    # Game API
    # Запуск игры в комнате
    path("api/game/rooms/<int:room_id>/start/", game_views.start_game, name="game-start"),

    # Управление игровой сессией
    path("api/game/sessions/<int:session_id>/", game_views.get_session, name="game-session-detail"),
    path("api/game/sessions/<int:session_id>/start/", game_views.start_session, name="game-session-start"),
    path("api/game/sessions/<int:session_id>/pause/", game_views.pause_session, name="game-session-pause"),
    path("api/game/sessions/<int:session_id>/resume/", game_views.resume_session, name="game-session-resume"),

    # Игровой процесс
    path("api/game/sessions/<int:session_id>/current-question/", game_views.get_current_question, name="game-current-question"),
    path("api/game/sessions/<int:session_id>/answer/", game_views.submit_answer, name="game-submit-answer"),
    path("api/game/sessions/<int:session_id>/results/", game_views.get_results, name="game-results"),

    # История игр
    path("api/game/sessions/my/", game_views.GameSessionListView.as_view(), name="my-game-sessions"),

    # Leaderboard (Таблица лидеров)
    path("api/leaderboard/global/", GlobalLeaderboardView.as_view(), name="global-leaderboard"),
    path("api/leaderboard/quiz/<int:quiz_id>/", QuizLeaderboardView.as_view(), name="quiz-leaderboard"),
    path("api/leaderboard/room/<int:room_id>/", RoomLeaderboardView.as_view(), name="room-leaderboard"),
    path("api/leaderboard/user/<int:user_id>/", UserStatsDetailView.as_view(), name="user-stats-detail"),
]

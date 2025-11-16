from django.contrib import admin
from .models import User, QuizBookmark, GameHistory


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "nickname", "total_points", "total_wins", "is_active", "is_staff")
    search_fields = ("email", "nickname")
    list_filter = ("is_active", "is_staff")
    readonly_fields = ("total_points", "total_wins")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль игрока", {"fields": ("nickname", "is_email_verified")}),
        ("Статистика", {"fields": ("total_points", "total_wins")}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nickname", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    ordering = ("id",)


@admin.register(QuizBookmark)
class QuizBookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "added_at")
    list_filter = ("added_at",)
    search_fields = ("user__email", "user__nickname", "quiz__title")
    readonly_fields = ("added_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "quiz")


@admin.register(GameHistory)
class GameHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "final_points", "accuracy", "final_rank", "played_at")
    list_filter = ("played_at", "final_rank")
    search_fields = ("user__email", "user__nickname", "quiz__title")
    readonly_fields = ("played_at", "accuracy")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "quiz", "room")



from django.contrib import admin
from django.utils.html import format_html
from .models import User, QuizBookmark, GameHistory, PasswordResetToken


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


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user_email", "token_short", "status_badge", "created_at", "expires_at", "time_left_display")
    list_filter = ("is_used", "created_at", "expires_at")
    search_fields = ("user__email", "user__nickname", "token")
    readonly_fields = ("token", "created_at", "expires_at", "used_at", "time_left_display", "is_valid_display")

    fieldsets = (
        ("Пользователь", {"fields": ("user",)}),
        ("Токен", {"fields": ("token", "is_valid_display", "time_left_display")}),
        ("Статус", {"fields": ("is_used", "used_at", "ip_address")}),
        ("Временные метки", {"fields": ("created_at", "expires_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email пользователя"
    user_email.admin_order_field = "user__email"

    def token_short(self, obj):
        return f"{obj.token[:12]}..."
    token_short.short_description = "Токен"

    def status_badge(self, obj):
        if obj.is_used:
            color = "gray"
            text = "Использован"
        elif obj.is_expired():
            color = "red"
            text = "Истек"
        else:
            color = "green"
            text = "Активен"
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, text
        )
    status_badge.short_description = "Статус"

    def time_left_display(self, obj):
        if obj.is_used or obj.is_expired():
            return "—"
        from django.utils import timezone
        delta = obj.expires_at - timezone.now()
        hours = delta.total_seconds() / 3600
        if hours < 1:
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes} мин"
        return f"{round(hours, 1)} ч"
    time_left_display.short_description = "Осталось времени"

    def is_valid_display(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green; font-weight: bold;">✓ Валиден</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Невалиден</span>')
    is_valid_display.short_description = "Валидность"


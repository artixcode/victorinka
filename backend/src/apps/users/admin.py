from django.contrib import admin
from .models import User


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

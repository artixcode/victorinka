from django.contrib import admin
from .models import GameSession, GameRound, PlayerAnswer, PlayerGameStats


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room",
        "quiz",
        "status",
        "current_question_index",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "created_at", "started_at")
    search_fields = ("room__name", "quiz__title")
    readonly_fields = ("created_at", "started_at", "finished_at")
    raw_id_fields = ("room", "quiz")

    fieldsets = (
        ("Основная информация", {
            "fields": ("room", "quiz", "status")
        }),
        ("Прогресс", {
            "fields": ("current_question_index",)
        }),
        ("Временные метки", {
            "fields": ("created_at", "started_at", "finished_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "round_number",
        "question_preview",
        "status",
        "first_answer_user",
        "time_limit",
        "started_at",
    )
    list_filter = ("status", "started_at")
    search_fields = ("session__id", "question__text")
    readonly_fields = ("started_at", "completed_at")
    raw_id_fields = ("session", "question", "first_answer_user")

    def question_preview(self, obj):
        return obj.question.text[:60] + "..." if len(obj.question.text) > 60 else obj.question.text
    question_preview.short_description = "Вопрос"

    fieldsets = (
        ("Основная информация", {
            "fields": ("session", "question", "round_number", "status")
        }),
        ("Настройки", {
            "fields": ("time_limit", "first_answer_user")
        }),
        ("Временные метки", {
            "fields": ("started_at", "completed_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(PlayerAnswer)
class PlayerAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "round",
        "is_correct",
        "points_earned",
        "time_taken",
        "answered_at",
    )
    list_filter = ("is_correct", "answered_at")
    search_fields = ("user__email", "user__nickname", "round__session__id")
    readonly_fields = ("answered_at", "points_earned")
    raw_id_fields = ("round", "user", "selected_option")

    fieldsets = (
        ("Основная информация", {
            "fields": ("round", "user", "selected_option")
        }),
        ("Результат", {
            "fields": ("is_correct", "points_earned", "time_taken")
        }),
        ("Временные метки", {
            "fields": ("answered_at",),
            "classes": ("collapse",)
        }),
    )


@admin.register(PlayerGameStats)
class PlayerGameStatsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session",
        "total_points",
        "correct_answers",
        "wrong_answers",
        "rank",
        "accuracy",
    )
    list_filter = ("rank", "completed_at")
    search_fields = ("user__email", "user__nickname", "session__id")
    readonly_fields = ("completed_at", "accuracy")
    raw_id_fields = ("session", "user")

    def accuracy(self, obj):
        total = obj.correct_answers + obj.wrong_answers
        if total == 0:
            return "0%"
        return f"{(obj.correct_answers / total * 100):.1f}%"
    accuracy.short_description = "Точность"

    fieldsets = (
        ("Основная информация", {
            "fields": ("session", "user", "rank")
        }),
        ("Статистика", {
            "fields": ("total_points", "correct_answers", "wrong_answers")
        }),
        ("Временные метки", {
            "fields": ("completed_at",),
            "classes": ("collapse",)
        }),
    )

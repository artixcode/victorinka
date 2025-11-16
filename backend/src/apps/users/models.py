from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager
from django.core.validators import MinValueValidator
from django.utils import timezone


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, db_index=True)

    nickname = models.CharField(max_length=40, unique=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    total_wins = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    total_points = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]

    objects = UserManager()

    def add_points(self, delta: int) -> None:
        new_value = self.total_points + int(delta)
        if new_value < 0:
            new_value = 0
        self.total_points = new_value

    def __str__(self):
        return self.email


class ActiveSession(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="sessions")
    refresh_jti = models.CharField(max_length=64, db_index=True)
    user_agent = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_seen_at",)
        indexes = [models.Index(fields=["user", "refresh_jti"])]

    def __str__(self):
        return f"{self.user.email} ({self.refresh_jti[:8]}...)"


class QuizBookmark(models.Model):
    """Закладки викторин пользователя"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quiz_bookmarks",
        verbose_name="Пользователь"
    )
    quiz = models.ForeignKey(
        "questions.Quiz",
        on_delete=models.CASCADE,
        related_name="bookmarked_by",
        verbose_name="Викторина"
    )
    added_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Добавлено в закладки"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Заметки",
        help_text="Личные заметки пользователя о викторине"
    )

    class Meta:
        verbose_name = "Закладка викторины"
        verbose_name_plural = "Закладки викторин"
        ordering = ["-added_at"]
        unique_together = [["user", "quiz"]]
        indexes = [
            models.Index(fields=["user", "-added_at"]),
            models.Index(fields=["user", "quiz"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} -> {self.quiz.title}"


class GameHistory(models.Model):
    """История игр пользователя"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="game_history",
        verbose_name="Пользователь"
    )
    session = models.ForeignKey(
        "game.GameSession",
        on_delete=models.CASCADE,
        related_name="history_entries",
        verbose_name="Игровая сессия"
    )
    room = models.ForeignKey(
        "rooms.Room",
        on_delete=models.CASCADE,
        related_name="history_entries",
        verbose_name="Комната"
    )
    quiz = models.ForeignKey(
        "questions.Quiz",
        on_delete=models.SET_NULL,
        null=True,
        related_name="history_entries",
        verbose_name="Викторина"
    )

    final_points = models.PositiveIntegerField(default=0, verbose_name="Финальные очки")
    correct_answers = models.PositiveIntegerField(default=0, verbose_name="Правильных ответов")
    total_questions = models.PositiveIntegerField(default=0, verbose_name="Всего вопросов")
    final_rank = models.PositiveIntegerField(null=True, blank=True, verbose_name="Место")

    played_at = models.DateTimeField(default=timezone.now, verbose_name="Дата игры")

    class Meta:
        verbose_name = "История игры"
        verbose_name_plural = "История игр"
        ordering = ["-played_at"]
        indexes = [
            models.Index(fields=["user", "-played_at"]),
            models.Index(fields=["user", "session"]),
        ]

    def __str__(self):
        quiz_title = self.quiz.title if self.quiz else "Удаленная викторина"
        return f"{self.user.nickname} - {quiz_title} ({self.played_at.strftime('%d.%m.%Y')})"

    @property
    def accuracy(self):
        """Процент правильных ответов"""
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 1)


from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class GameSession(models.Model):

    class Status(models.TextChoices):
        WAITING = "waiting", "Ожидание"
        PLAYING = "playing", "Идёт игра"
        PAUSED = "paused", "Пауза"
        FINISHED = "finished", "Завершена"

    room = models.ForeignKey(
        "rooms.Room",
        on_delete=models.CASCADE,
        related_name="game_sessions",
        help_text="Комната, в которой проходит игра"
    )
    quiz = models.ForeignKey(
        "questions.Quiz",
        on_delete=models.PROTECT,
        related_name="game_sessions",
        help_text="Викторина, которая используется в игре"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
        db_index=True
    )
    current_question_index = models.PositiveIntegerField(
        default=0,
        help_text="Индекс текущего вопроса (0-based)"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["room", "status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Game #{self.pk}: {self.quiz.title} in {self.room.name} ({self.get_status_display()})"

    def start(self):
        if self.status == self.Status.WAITING:
            self.status = self.Status.PLAYING
            self.started_at = timezone.now()
            self.save(update_fields=["status", "started_at"])

    def pause(self):
        if self.status == self.Status.PLAYING:
            self.status = self.Status.PAUSED
            self.save(update_fields=["status"])

    def resume(self):
        if self.status == self.Status.PAUSED:
            self.status = self.Status.PLAYING
            self.save(update_fields=["status"])

    def finish(self):
        if self.status in [self.Status.PLAYING, self.Status.PAUSED]:
            self.status = self.Status.FINISHED
            self.finished_at = timezone.now()
            self.save(update_fields=["status", "finished_at"])


class GameRound(models.Model):

    class Status(models.TextChoices):
        WAITING = "waiting", "Ожидание"
        ACTIVE = "active", "Активный"
        COMPLETED = "completed", "Завершён"

    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="rounds",
        help_text="Игровая сессия"
    )
    question = models.ForeignKey(
        "questions.Question",
        on_delete=models.PROTECT,
        related_name="game_rounds",
        help_text="Вопрос в этом раунде"
    )
    round_number = models.PositiveIntegerField(
        help_text="Номер раунда (1-based)",
        validators=[MinValueValidator(1)]
    )
    time_limit = models.PositiveIntegerField(
        default=30,
        help_text="Лимит времени на ответ (в секундах)",
        validators=[MinValueValidator(5)]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )
    first_answer_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="first_answers",
        help_text="Игрок, ответивший первым"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["session", "round_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "round_number"],
                name="uq_game_round_session_number"
            )
        ]
        indexes = [
            models.Index(fields=["session", "status"]),
        ]

    def __str__(self):
        return f"Round #{self.round_number} in Game #{self.session_id}: {self.question.text[:50]}"

    def start(self):
        if self.status == self.Status.WAITING:
            self.status = self.Status.ACTIVE
            self.started_at = timezone.now()
            self.save(update_fields=["status", "started_at"])

    def complete(self):
        if self.status == self.Status.ACTIVE:
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at"])


class PlayerAnswer(models.Model):

    round = models.ForeignKey(
        GameRound,
        on_delete=models.CASCADE,
        related_name="answers",
        help_text="Раунд игры"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="game_answers",
        help_text="Игрок"
    )
    selected_option = models.ForeignKey(
        "questions.AnswerOption",
        on_delete=models.PROTECT,
        related_name="player_selections",
        help_text="Выбранный вариант ответа"
    )
    is_correct = models.BooleanField(
        default=False,
        help_text="Правильный ли ответ"
    )
    points_earned = models.PositiveIntegerField(
        default=0,
        help_text="Очки, заработанные за ответ"
    )
    time_taken = models.FloatField(
        help_text="Время, затраченное на ответ (в секундах)",
        validators=[MinValueValidator(0.0)]
    )
    answered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["answered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["round", "user"],
                name="uq_player_answer_round_user"
            )
        ]
        indexes = [
            models.Index(fields=["round", "user"]),
            models.Index(fields=["user", "-answered_at"]),
        ]

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.user} answered in Round #{self.round.round_number} (+{self.points_earned} pts)"

    def calculate_points(self):

        if not self.is_correct:
            self.points_earned = 0
            return 0

        base_points = self.round.question.points
        time_limit = self.round.time_limit

        # Бонус за скорость: чем быстрее ответ, тем больше бонус
        # Максимум +50% к базовым очкам
        if self.time_taken < time_limit:
            speed_bonus_ratio = (time_limit - self.time_taken) / time_limit
            speed_bonus = int(base_points * speed_bonus_ratio * 0.5)
        else:
            speed_bonus = 0

        # Бонус за первый правильный ответ: +50%
        first_answer_bonus = 0
        if self.user_id == self.round.first_answer_user_id:
            first_answer_bonus = int(base_points * 0.5)

        total_points = base_points + speed_bonus + first_answer_bonus
        self.points_earned = total_points
        return total_points


class PlayerGameStats(models.Model):

    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="player_stats",
        help_text="Игровая сессия"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="game_stats",
        help_text="Игрок"
    )
    total_points = models.PositiveIntegerField(
        default=0,
        help_text="Всего очков в этой игре"
    )
    correct_answers = models.PositiveIntegerField(
        default=0,
        help_text="Количество правильных ответов"
    )
    wrong_answers = models.PositiveIntegerField(
        default=0,
        help_text="Количество неправильных ответов"
    )
    rank = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Место игрока в этой игре (1 = победитель)"
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-total_points", "completed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "user"],
                name="uq_player_stats_session_user"
            )
        ]
        indexes = [
            models.Index(fields=["session", "-total_points"]),
            models.Index(fields=["user", "-total_points"]),
        ]
        verbose_name = "Player Game Statistics"
        verbose_name_plural = "Player Game Statistics"

    def __str__(self):
        return f"{self.user} in Game #{self.session_id}: {self.total_points} pts (Rank: {self.rank or 'TBD'})"

    def update_from_answer(self, answer: PlayerAnswer):
        if answer.is_correct:
            self.correct_answers += 1
        else:
            self.wrong_answers += 1

        self.total_points += answer.points_earned
        self.save(update_fields=["total_points", "correct_answers", "wrong_answers"])

    def finalize(self):
        self.completed_at = timezone.now()
        self.save(update_fields=["completed_at"])


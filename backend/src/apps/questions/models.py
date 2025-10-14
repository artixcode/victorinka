from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


class Topic(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:90]
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:60]
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Quiz(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Публичная"
        PRIVATE = "private", "Приватная"

    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликована"
        ARCHIVED = "archived", "Архив"

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=140, db_index=True)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PUBLIC, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)

    topics = models.ManyToManyField(Topic, related_name="quizzes", blank=True)
    tags = models.ManyToManyField(Tag, related_name="quizzes", blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    questions = models.ManyToManyField(
        "Question",
        through="QuizQuestion",
        related_name="in_quizzes",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "status"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def publish(self):
        self.status = Quiz.Status.PUBLISHED
        self.save(update_fields=["status"])

    def archive(self):
        self.status = Quiz.Status.ARCHIVED
        self.save(update_fields=["status"])


class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Лёгкий"
        MEDIUM = "medium", "Средний"
        HARD = "hard", "Сложный"

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "difficulty"]),
        ]

    def __str__(self):
        return f"Q{self.pk}: {self.text[:50]}"


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(4)])

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["question", "order"], name="uq_option_question_order"),
            models.UniqueConstraint(
                fields=["question", "is_correct"],
                condition=Q(is_correct=True),
                name="uq_option_one_correct_per_question",
            ),
        ]

    def __str__(self):
        prefix = "✓" if self.is_correct else "•"
        return f"{prefix} {self.text[:60]}"


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, help_text="Порядок вопроса в викторине")

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["quiz", "question"], name="uq_quiz_question"),
            models.UniqueConstraint(fields=["quiz", "order"], name="uq_quiz_order"),
        ]

    def __str__(self):
        return f"{self.quiz.title} -> Q{self.question_id} (#{self.order})"

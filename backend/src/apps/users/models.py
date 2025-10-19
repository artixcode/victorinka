from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager
from django.core.validators import MinValueValidator


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

from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, db_index=True)

    full_name = models.CharField(max_length=150, blank=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

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
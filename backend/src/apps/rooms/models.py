from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets
import string

User = settings.AUTH_USER_MODEL

def gen_invite_code(length: int = 6) -> str:

    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class Room(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        OPEN = "open", "Открыта"
        IN_PROGRESS = "in_progress", "Идёт"
        FINISHED = "finished", "Завершена"

    name = models.CharField(max_length=120)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hosted_rooms")
    invite_code = models.CharField(max_length=12, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            code = gen_invite_code()
            while Room.objects.filter(invite_code=code).exists():
                code = gen_invite_code()
            self.invite_code = code
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.invite_code})"


class RoomParticipant(models.Model):
    class Role(models.TextChoices):
        HOST = "host", "Хост"
        PLAYER = "player", "Игрок"

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="room_participations")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PLAYER)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("room", "user")

    def __str__(self) -> str:
        return f"{self.user} in {self.room} as {self.role}"

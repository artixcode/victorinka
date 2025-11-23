from celery import shared_task
from django.utils import timezone


@shared_task(name='apps.core.tasks.cleanup_expired_tokens')
def cleanup_expired_tokens():
    """
    Очистка истекших JWT токенов из базы данных
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

        deleted_count, _ = OutstandingToken.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()

        return f"Удалено {deleted_count} истекших токенов"

    except Exception as e:
        return f"Ошибка при очистке токенов: {str(e)}"


@shared_task(name='apps.core.tasks.test_celery')
def test_celery(message: str = "Hello from Celery!"):
    """
    Тестовая задача для проверки работы Celery
    """
    print(f"Celery работает! Сообщение: {message}")
    return {
        "status": "success",
        "message": message,
        "timestamp": timezone.now().isoformat()
    }


@shared_task(name='apps.core.tasks.send_test_notification')
def send_test_notification(user_id: int, text: str):
    """
    Тестовая задача отправки уведомления
    """
    print(f"Отправка уведомления пользователю {user_id}: {text}")


    return {
        "status": "sent",
        "user_id": user_id,
        "text": text,
        "sent_at": timezone.now().isoformat()
    }


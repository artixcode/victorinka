import os
from celery import Celery
from celery.schedules import crontab
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('victorinka')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


# Настройка периодических задач (Celery Beat)
app.conf.beat_schedule = {
    'cleanup-old-game-sessions': {
        'task': 'apps.game.tasks.cleanup_old_game_sessions',
        'schedule': crontab(minute=0),  # Каждый час
    },
    'notify-inactive-players': {
        'task': 'apps.game.tasks.notify_inactive_players',
        'schedule': crontab(minute='*/30'),  # Каждые 30 минут
    },
}

app.conf.timezone = 'UTC'


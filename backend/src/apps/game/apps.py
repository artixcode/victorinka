from django.apps import AppConfig


class GameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.game'

    def ready(self):
        from apps.game.application.event_handlers.setup import setup_event_handlers

        setup_event_handlers()

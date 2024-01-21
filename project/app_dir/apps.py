from django.apps import AppConfig


class AppDirConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_dir'

    def ready(self):
        import app_dir.signals
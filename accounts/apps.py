from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "accounts"
    verbose_name = "Accounts"

    def ready(self):
        # import signals so post_save hooks register
        from . import signals  # noqa: F401

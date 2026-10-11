from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
    verbose_name = "Core"

    def ready(self) -> None:
        # Sandbox-only: bridge the preview gateway port to the auto-started
        # dev server. Triple-guarded + failure-proof; no-op everywhere else.
        from . import preview_bridge

        preview_bridge.maybe_start()

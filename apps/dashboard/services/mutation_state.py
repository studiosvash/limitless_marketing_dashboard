"""Per-project mutation state (alert acks, hidden audit checks, ads overrides).

Backed by the same ProjectSettings JSON blob the Settings groups use — these are
first-party app state, not analytics, so they live in django_internal.db. Keys are
distinct from every Settings group name routed by settings_service.apply_settings_update
("alertAcks", "auditHidden", "adsOverrides"), so a Settings PUT can never clobber them.
"""
from apps.dashboard.models import ProjectSettings


def get_state(site_id: str, key: str, default):
    obj = ProjectSettings.objects.filter(site_url=site_id).first()
    if obj is None:
        return default
    return obj.data.get(key, default)


def set_state(site_id: str, key: str, value) -> None:
    obj, _ = ProjectSettings.objects.get_or_create(site_url=site_id, defaults={"data": {}})
    obj.data[key] = value
    obj.save(update_fields=["data", "updated_at"])

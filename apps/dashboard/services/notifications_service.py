"""Topbar bell — apps.dashboard.models.Notification (Django ORM, django_internal.db).

Separate from alerts_service.py on purpose (see Notification's docstring): the bell used to
mirror the Alerts feed, which meant it repeated anomaly/technical rows the Alerts page and
its sidebar badge already own. This module is the only writer/reader of the leaner event set
the bell now shows: connection failures, a refresh finishing (success or error), budget/
balance crossings, and a teammate being added.

`notify()` is the single write path and is deliberately never allowed to raise — every call
site is inside a sync, a cost-recording hook, or an account-creation transaction, none of
which may fail because a bell row could not be written.
"""
import logging

from apps.dashboard.models import Notification

logger = logging.getLogger(__name__)

FEED_LIMIT = 30


def notify(kind: str, title: str, detail: str = "", severity: str = "info", site_url: str = "") -> None:
    """Write one Notification row. Swallows everything — see module docstring."""
    try:
        Notification.objects.create(
            site_url=site_url or "", kind=kind, severity=severity, title=title, detail=detail,
        )
    except Exception:
        logger.error("notifications_service.notify failed", exc_info=True)


def build_notifications_response() -> dict:
    """{"items": [{id, kind, severity, title, detail, ts, read}], "unread": n}

    Newest first, capped at FEED_LIMIT — this is a bell dropdown, not an archive. `unread`
    counts every unread row, not just the ones shown, so the badge stays correct even past
    the cap.
    """
    try:
        unread = Notification.objects.filter(read=False).count()
        rows = Notification.objects.all()[:FEED_LIMIT]
        items = [
            {
                "id": n.pk, "kind": n.kind, "severity": n.severity,
                "title": n.title, "detail": n.detail,
                "ts": n.created_at.isoformat(), "read": n.read,
            }
            for n in rows
        ]
        return {"items": items, "unread": unread}
    except Exception:
        logger.error("build_notifications_response failed", exc_info=True)
        return {"items": [], "unread": 0}


def mark_read(notification_id: int) -> None:
    try:
        Notification.objects.filter(pk=notification_id).update(read=True)
    except Exception:
        logger.error("mark_read failed", exc_info=True)


def mark_all_read() -> None:
    try:
        Notification.objects.filter(read=False).update(read=True)
    except Exception:
        logger.error("mark_all_read failed", exc_info=True)

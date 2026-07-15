"""
pipeline/connectors/base.py — BaseConnector for all API connectors.

The sync() method writes status updates to Django's sync.SyncLog model
(django_internal.db) so the HTMX progress bar can read them via Django views.
Analytics data is written to fusehealth.db via SQLAlchemy (_write_records).
"""
import time
from typing import Optional

from pipeline.utils.logger import get_logger
from pipeline.utils.db_connection import get_session


def _update_django_sync_log(connector: str, site_url: str, status: str, **kwargs) -> None:
    """Write a SyncLog row to Django's django_internal.db. Silent no-op when Django is not available."""
    try:
        from apps.sync.models import SyncLog
        from django.utils import timezone
        obj, _ = SyncLog.objects.update_or_create(
            connector=connector,
            site_url=site_url,
            defaults={
                "status": status,
                "last_synced": timezone.now() if status in ("success", "error") else None,
                # error_message may be an EXPLICIT None (success path clearing a previous
                # failure) — dropping None here made stale error text stick to success rows
                # forever, which Settings → Connections then displayed as a live problem.
                **{k: v for k, v in kwargs.items() if v is not None or k == "error_message"},
            },
        )
    except ImportError:
        pass  # Non-Django context (standalone scripts, tests)
    except Exception as exc:
        import logging
        logging.getLogger("fusehealth.base").warning(f"[{connector}] SyncLog update failed: {exc}")


class BaseConnector:
    """
    Abstract base for all API connectors.

    Subclasses must define:
        name (str): Short lowercase identifier, e.g. 'gsc', 'meta'
        fetch(site_id=None, **kwargs) -> list[dict]: Calls the API, returns normalized records.

    Subclasses should override _write_records to call the correct pipeline.db.writer function.
    """

    name: str = "base"

    def __init__(self):
        self.logger = get_logger(self.name)

    def fetch(self, site_id: Optional[str] = None, **kwargs) -> list[dict]:
        raise NotImplementedError(f"[{self.name}] fetch() not implemented.")

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return 0

    def sync(self, site_id: Optional[str] = None, **kwargs) -> dict:
        """
        Full sync cycle: fetch → write → log. Scoped to a single site.
        Writes status to Django SyncLog and analytics data to fusehealth.db.
        """
        site_tag = f" [{site_id}]" if site_id else ""
        self.logger.info(f"[{self.name}]{site_tag} Sync started")
        start_time = time.monotonic()

        _update_django_sync_log(self.name, site_id or "", "running")

        try:
            records = self.fetch(site_id=site_id, **kwargs)
            records_written = 0

            with get_session() as session:
                records_written = self._write_records(session, records, site_id=site_id)

            duration = round(time.monotonic() - start_time, 2)
            self.logger.info(
                f"[{self.name}]{site_tag} Sync complete — {records_written} records | {duration}s"
            )

            _update_django_sync_log(
                self.name, site_id or "", "success",
                records_written=records_written,
                duration_seconds=duration,
                error_message=None,
            )

            return {
                "status": "success",
                "site_id": site_id or "",
                "records_written": records_written,
                "duration_seconds": duration,
                "error": None,
            }

        except Exception as exc:
            duration = round(time.monotonic() - start_time, 2)
            error_msg = str(exc)
            self.logger.error(f"[{self.name}]{site_tag} Sync failed after {duration}s: {error_msg}")

            _update_django_sync_log(
                self.name, site_id or "", "error",
                error_message=error_msg,
                duration_seconds=duration,
            )

            return {
                "status": "error",
                "site_id": site_id or "",
                "records_written": 0,
                "duration_seconds": duration,
                "error": error_msg,
            }

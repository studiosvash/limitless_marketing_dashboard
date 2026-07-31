"""Test runner that cleans up after the suite's temporary analytics databases.

Why this exists
---------------
Every test that touches analytics data builds its own throwaway SQLite file, using the
fixture documented in .claude/skills.md §8:

    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))

The fixture registers `addCleanup` for the *session factory* and the `override_settings`
context, but nothing ever removes the directory. There are 58 of those call sites across 34
test modules, so a single full run leaves ~250 directories behind, each holding a 0.5-1 MB
database. That is invisible for a while and then it is not: this repo accumulated 29 216 of
them (16.6 GB) and filled the system drive to zero bytes, at which point the suite could no
longer run at all.

Rather than patch 58 call sites — and rely on every future test remembering — this points
`tempfile` itself at one run-scoped directory and deletes that directory when the suite ends.
`tempfile.mkdtemp()` with no `dir=` argument resolves `tempfile.tempdir` at call time, so
every existing and future call site is covered without changing any of them.

Deliberately NOT a shared TestCase base class: this project's test-hygiene rule is that every
test class inherits directly from TestCase/APITestCase and never from a sibling, so there is
no shared base to hang teardown on.
"""

import gc
import shutil
import tempfile
from pathlib import Path

from django.test.runner import DiscoverRunner


def _release_sqlite_handles():
    """Close what still holds the temp SQLite files open, so Windows will let them go.

    Windows refuses to delete a file with an open handle, and each test's engine keeps its
    connection pooled. `pipeline.utils.db_connection._SessionFactory` is a module-level
    singleton the fixtures reset to None without ever disposing — that drops the reference
    but not necessarily the OS handle — and every per-test engine is unreferenced garbage by
    now. Dispose the one we can reach, then collect the rest.
    """
    try:
        import pipeline.utils.db_connection as db_connection
        factory = getattr(db_connection, "_SessionFactory", None)
        bind = getattr(factory, "kw", {}).get("bind") if factory is not None else None
        if bind is not None:
            bind.dispose()
        db_connection._SessionFactory = None
    except Exception:
        pass  # best-effort: never fail a green suite over cleanup
    gc.collect()


class TempCleaningRunner(DiscoverRunner):
    """DiscoverRunner that confines the suite's temp files to one directory and removes it."""

    _temp_root: str | None = None
    _previous_tempdir = None

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._previous_tempdir = tempfile.tempdir
        # Created under the real system temp dir, so it inherits the platform's own
        # permissions and lands on whichever volume temp files are supposed to use.
        self._temp_root = tempfile.mkdtemp(prefix="fusehealth-tests-", dir=self._previous_tempdir)
        tempfile.tempdir = self._temp_root

    def teardown_test_environment(self, **kwargs):
        tempfile.tempdir = self._previous_tempdir
        if self._temp_root:
            _release_sqlite_handles()
            leftover = Path(self._temp_root)
            # Two passes: the first drops everything not still held open, and the collect
            # between them gives any engine freed by that pass a chance to close. Never
            # raises — a cleanup failure must not turn a green suite red, and whatever
            # survives is still confined to this one directory, so the next run's mess is
            # bounded instead of unbounded.
            for _ in range(2):
                shutil.rmtree(leftover, ignore_errors=True)
                if not leftover.exists():
                    break
                gc.collect()
            if leftover.exists():
                print(f"[tests] could not fully remove {leftover} — safe to delete manually")
            self._temp_root = None
        super().teardown_test_environment(**kwargs)

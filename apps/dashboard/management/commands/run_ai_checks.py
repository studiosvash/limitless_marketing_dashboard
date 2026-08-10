"""Execute one planned AI-visibility run in its own OS process.

    python manage.py run_ai_checks --site-url sc-domain:example.com --task-id ab12cd34

WHY THIS COMMAND EXISTS
-----------------------
`POST /ai/run` used to do the whole run inline: every tracked prompt x every tracked answer
engine, strictly sequentially, each DataForSEO call allowed up to `REQUEST_TIMEOUT = 120`
seconds. Fifteen prompts across four engines is sixty sequential calls — 8-15 minutes inside a
single HTTP request. Three things then went wrong together:

  * nginx / gunicorn / Cloudflare killed the request long before the loop finished. The SPA's
    `aiRunning` flag was only ever cleared in `.then`/`.catch`, so after that every Run button
    on the page was a silent no-op relabelled "Running…" for the rest of the session.
  * results were persisted ONCE, after the entire loop. A worker killed at check 41 of 60
    discarded 40 checks DataForSEO had already billed.
  * a run that really did finish server-side looked, in the browser, like nothing happened.

As its own process the run outlives the web worker that received the click — exactly the
reasoning (and exactly the mechanism) behind `manage.py run_sync`, which this command is
modelled on. The task state in `ProjectSettings.data` is the only channel between the request
and this process, so it carries the plan; the worker writes progress back to it after every
prompt, and the SPA reads it off the ordinary AI GET.

Directly runnable by an operator, which is how you debug a failing run: you get the full
traceback on your terminal instead of one line in the UI.
"""
import logging
import traceback

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the planned answer-engine checks for one recorded AI run task."

    def add_arguments(self, parser):
        parser.add_argument("--site-url", required=True,
                            help="Site.site_url the run belongs to.")
        parser.add_argument("--task-id", required=True,
                            help="Id of the run task recorded in ProjectSettings.data.")

    def handle(self, *args, **options):
        from apps.dashboard.services.ai_service import (
            RUN_TASK_KEY, execute_ai_run, get_state, set_state, _now_iso,
        )

        site_url = options["site_url"]
        task_id = options["task_id"]

        task = get_state(site_url, RUN_TASK_KEY, None)
        if not isinstance(task, dict) or task.get("taskId") != task_id:
            # Not an error: a newer run may have taken over between the spawn and here.
            self.stdout.write(f"AI run {task_id} is not the current task for {site_url!r} "
                              "— nothing to do.")
            return
        if task.get("state") != "running":
            self.stdout.write(f"AI run {task_id} is already {task.get('state')} "
                              "— nothing to do.")
            return

        self.stdout.write(f"Running {task.get('total', 0)} planned check(s) for {site_url!r} "
                          f"(task {task_id})…")
        try:
            summary = execute_ai_run(site_url, task_id)
        except Exception:
            # execute_ai_run marks the task on the paths it controls, but a crash outside them
            # (a DB outage, an import error) would otherwise leave the task at `running`
            # forever — which disables every Run button in the SPA until the pid reaper clears
            # it. That is the failure mode this whole change exists to end.
            tb = traceback.format_exc()
            logger.error("[run_ai_checks] run %s crashed:\n%s", task_id, tb)
            last_line = tb.strip().splitlines()[-1] if tb.strip() else "unknown error"
            current = get_state(site_url, RUN_TASK_KEY, None)
            if isinstance(current, dict) and current.get("taskId") == task_id \
                    and current.get("state") == "running":
                set_state(site_url, RUN_TASK_KEY, {
                    **current, "state": "error", "current": None, "finishedAt": _now_iso(),
                    "error": f"The run process crashed: {last_line}",
                })
            raise CommandError(f"AI run crashed — see the log. {last_line}")

        self.stdout.write(self.style.SUCCESS(
            f"Done: {summary['checked']} check(s) answered, ${summary['cost']:.4f} recorded."
        ))
        if summary.get("detail"):
            self.stdout.write(self.style.WARNING(f"  ! {summary['detail']}"))

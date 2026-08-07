# Data migration: prompt checks moved from a direct OpenAI call (only chatgpt connectable)
# to DataForSEO's LLM Responses API (all four engines connectable with the same credentials).
#
# Prompts created before that change were seeded tracked_models=["chatgpt"] purely because
# connectable_platforms() returned only chatgpt at the time — not because anyone chose to
# exclude the other engines. Expand exactly those rows to the full set, and leave any other
# combination alone: a list that differs from ["chatgpt"] was actively edited in the config
# modal and is a real preference.

from django.db import migrations

ALL_ENGINES = ["chatgpt", "claude", "gemini", "perplexity"]


def expand_default_tracked_models(apps, schema_editor):
    AIPrompt = apps.get_model("dashboard", "AIPrompt")
    for prompt in AIPrompt.objects.filter(tracked_models=["chatgpt"]):
        prompt.tracked_models = list(ALL_ENGINES)
        prompt.save(update_fields=["tracked_models"])


def restore_chatgpt_only(apps, schema_editor):
    AIPrompt = apps.get_model("dashboard", "AIPrompt")
    for prompt in AIPrompt.objects.filter(tracked_models=ALL_ENGINES):
        prompt.tracked_models = ["chatgpt"]
        prompt.save(update_fields=["tracked_models"])


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0005_budgetstate_notification"),
    ]

    operations = [
        migrations.RunPython(expand_default_tracked_models, restore_chatgpt_only),
    ]

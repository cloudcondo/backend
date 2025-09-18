from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_safe_cleanup_and_updated_at"),
    ]

    operations = [
        # Make Django aware of the field again (state only; no DB change here).
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="parkingspot",
                    name="notes",
                    field=models.TextField(blank=True, null=True, default=""),
                ),
            ],
            database_operations=[],
        ),
        # Now actually drop it (SQLite will recreate the table).
        migrations.RemoveField(
            model_name="parkingspot",
            name="notes",
        ),
    ]

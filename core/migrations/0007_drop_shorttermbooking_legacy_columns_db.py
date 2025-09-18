from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_remove_parkingspot_notes_db"),
    ]

    operations = [
        # 1) Re-introduce legacy fields in *state only* so Django "knows" them.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="shorttermbooking",
                    name="approved_at",
                    field=models.DateTimeField(null=True, blank=True, default=None),
                ),
                migrations.AddField(
                    model_name="shorttermbooking",
                    name="approved_by",
                    field=models.CharField(
                        max_length=255, null=True, blank=True, default=""
                    ),
                ),
                migrations.AddField(
                    model_name="shorttermbooking",
                    name="created_by_email",
                    field=models.CharField(
                        max_length=255, null=True, blank=True, default=""
                    ),
                ),
                migrations.AddField(
                    model_name="shorttermbooking",
                    name="guest_email",
                    field=models.CharField(
                        max_length=255, null=True, blank=True, default=""
                    ),
                ),
                migrations.AddField(
                    model_name="shorttermbooking",
                    name="guest_phone",
                    field=models.CharField(
                        max_length=50, null=True, blank=True, default=""
                    ),
                ),
                migrations.AddField(
                    model_name="shorttermbooking",
                    name="id_city",
                    field=models.CharField(
                        max_length=255, null=True, blank=True, default=""
                    ),
                ),
                migrations.AddField(
                    model_name="shorttermbooking",
                    name="num_guests",
                    field=models.IntegerField(null=True, blank=True, default=None),
                ),
            ],
            database_operations=[],
        ),
        # 2) Now actually remove them (DB operation). On SQLite this rebuilds the table
        # without these columns, eliminating NOT NULL constraints left behind.
        migrations.RemoveField(model_name="shorttermbooking", name="approved_at"),
        migrations.RemoveField(model_name="shorttermbooking", name="approved_by"),
        migrations.RemoveField(model_name="shorttermbooking", name="created_by_email"),
        migrations.RemoveField(model_name="shorttermbooking", name="guest_email"),
        migrations.RemoveField(model_name="shorttermbooking", name="guest_phone"),
        migrations.RemoveField(model_name="shorttermbooking", name="id_city"),
        migrations.RemoveField(model_name="shorttermbooking", name="num_guests"),
    ]

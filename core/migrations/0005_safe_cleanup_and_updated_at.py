from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_alter_shorttermbooking_dates_to_datefield"),
    ]

    operations = [
        # Add updated_at to all models (aligns with your models.py)
        migrations.AddField(
            model_name="condo",
            name="updated_at",
            field=models.DateTimeField(default=timezone.now, auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="unit",
            name="updated_at",
            field=models.DateTimeField(default=timezone.now, auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="parkingspot",
            name="updated_at",
            field=models.DateTimeField(default=timezone.now, auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="unitparkingassignment",
            name="updated_at",
            field=models.DateTimeField(default=timezone.now, auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="shorttermbooking",
            name="updated_at",
            field=models.DateTimeField(default=timezone.now, auto_now=True),
            preserve_default=False,
        ),
        # Don’t try to DROP columns in SQLite that never existed.
        # Update Django state only so future migrations stay consistent.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name="parkingspot", name="notes"),
                migrations.RemoveField(
                    model_name="shorttermbooking", name="approved_at"
                ),
                migrations.RemoveField(
                    model_name="shorttermbooking", name="approved_by"
                ),
                migrations.RemoveField(
                    model_name="shorttermbooking", name="created_by_email"
                ),
                migrations.RemoveField(
                    model_name="shorttermbooking", name="guest_email"
                ),
                migrations.RemoveField(
                    model_name="shorttermbooking", name="guest_phone"
                ),
                migrations.RemoveField(model_name="shorttermbooking", name="id_city"),
                migrations.RemoveField(
                    model_name="shorttermbooking", name="num_guests"
                ),
            ]
        ),
    ]

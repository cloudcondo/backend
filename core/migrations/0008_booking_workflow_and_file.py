import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    # Make 0008 depend on 0007 to linearize the graph.
    dependencies = [
        ("core", "0007_drop_shorttermbooking_legacy_columns_db"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Workflow fields
        migrations.AddField(
            model_name="shorttermbooking",
            name="submitted_by",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name="bookings_submitted",
            ),
        ),
        migrations.AddField(
            model_name="shorttermbooking",
            name="reviewed_by",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name="bookings_reviewed",
            ),
        ),
        migrations.AddField(
            model_name="shorttermbooking",
            name="reviewed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        # Optional ID upload
        migrations.AddField(
            model_name="shorttermbooking",
            name="id_document",
            field=models.FileField(upload_to="ids/", null=True, blank=True),
        ),
        # Normalize statuses (lowercase)
        migrations.AlterField(
            model_name="shorttermbooking",
            name="status",
            field=models.CharField(
                max_length=16,
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
            ),
        ),
    ]

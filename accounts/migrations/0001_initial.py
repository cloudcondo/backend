import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    # Make sure core tables exist first (Unit/Condo)
    dependencies = [
        (
            "core",
            "0006_remove_parkingspot_notes_db",
        ),  # safe, already applied in your project
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("pm", "Property Manager"),
                            ("concierge", "Concierge"),
                            ("owner", "Owner"),
                            ("guest", "Guest"),
                            ("partner", "Rental Manager / Partner"),
                        ],
                        default="guest",
                        max_length=20,
                    ),
                ),
                ("phone", models.CharField(blank=True, default="", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "condo",
                    models.ForeignKey(
                        blank=True,
                        help_text="Primary condo this user is associated with (optional).",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.condo",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "User Profile",
                "verbose_name_plural": "User Profiles",
                "db_table": "accounts_userprofile",
            },
        ),
        migrations.CreateModel(
            name="UnitAccess",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "access_type",
                    models.CharField(
                        choices=[
                            ("owner", "Owner"),
                            ("rental_manager", "Rental Manager"),
                            ("tenant", "Tenant"),
                            ("guest_submitter", "Guest Submitter"),
                        ],
                        default="owner",
                        max_length=20,
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accesses",
                        to="core.unit",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unit_accesses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Unit Access",
                "verbose_name_plural": "Unit Access",
                "db_table": "accounts_unitaccess",
                "unique_together": {("user", "unit", "access_type")},
            },
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_parkingspot_shorttermbooking_unitparkingassignment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shorttermbooking",
            name="check_in",
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name="shorttermbooking",
            name="check_out",
            field=models.DateField(),
        ),
    ]

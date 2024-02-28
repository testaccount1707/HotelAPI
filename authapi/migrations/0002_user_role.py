# Generated by Django 5.0.2 on 2024-02-28 05:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authapi", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="role",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[(1, "Admin"), (2, "Manager"), (3, "Employee")],
                default=3,
                null=True,
            ),
        ),
    ]
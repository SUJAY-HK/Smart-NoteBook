# Generated by Django 5.2 on 2025-04-09 10:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="sketch",
            name="created_by",
            field=models.ForeignKey(
                default=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="sketch",
            name="name",
            field=models.CharField(default="test", max_length=100),
        ),
        migrations.AlterField(
            model_name="sketch",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="sketches/"),
        ),
        migrations.AlterField(
            model_name="sketch",
            name="strokes",
            field=models.JSONField(default=list),
        ),
    ]

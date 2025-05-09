# Generated by Django 5.2 on 2025-04-10 10:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_rename_timestamp_sketch_created_at_remove_book_title_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sketch",
            name="book",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sketches",
                to="app.book",
            ),
        ),
    ]

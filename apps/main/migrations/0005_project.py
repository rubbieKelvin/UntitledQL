# Generated by Django 4.1 on 2022-09-04 17:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_update_user_roles"),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=35)),
                ("description", models.CharField(default="", max_length=250)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                ("is_archived", models.BooleanField(default=False)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projects",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

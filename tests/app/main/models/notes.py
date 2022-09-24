from uuid import uuid4
from django.db import models


class Note(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    name = models.CharField(max_length=35)
    content = models.CharField(max_length=250, default="")
    starred = models.BooleanField(default=False)
    author = models.ForeignKey(
        "main.User", on_delete=models.CASCADE, related_name="notes"
    )
    last_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

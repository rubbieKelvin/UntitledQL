from uuid import uuid4
from django.db import models

class Project(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    name = models.CharField(max_length=35)
    description = models.CharField(max_length=250, default="")
    author = models.ForeignKey('main.User', on_delete=models.CASCADE, related_name="projects")
    last_updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name
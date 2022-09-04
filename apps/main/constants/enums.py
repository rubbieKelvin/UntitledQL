from django.db.models import TextChoices


class UserRoles(TextChoices):
    ADMIN = "admin"
    USER = "user"

from django.db.models import TextChoices

class UserRoles(TextChoices):
    ADMIN = "ADMIN"
    USER = "USER"

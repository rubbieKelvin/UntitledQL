from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from uuid import uuid4
from main.constants.enums import UserRoles
from main.managers.users import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(default=uuid4, primary_key=True)
    email = models.EmailField("email address", unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    role = models.CharField(
        max_length=5, choices=UserRoles.choices, default=UserRoles.USER
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

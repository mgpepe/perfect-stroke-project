from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    picture_url = models.URLField(blank=True)
    birthday = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    facebook_id = models.BigIntegerField(null=True, blank=True, unique=True)

    class Meta:
        db_table = 'users'

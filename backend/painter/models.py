"""Database models for the Wonder Painter backend."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    """Wonder Painter-specific fields attached to Django's auth user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    email_key = models.CharField(max_length=254, unique=True, editable=False)
    nickname = models.CharField(max_length=25)
    avatar = models.ImageField(upload_to="avatars", blank=True)

    def __str__(self):
        return self.user.username


class EmailVerification(models.Model):
    """A single-use, hashed email-verification token for a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
    )
    token_digest = models.CharField(max_length=64, unique=True)
    sent_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Email verification for {self.user.username}"

"""Input validation for the public API."""

from uuid import uuid4

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


class RegistrationForm(forms.Form):
    username = forms.CharField(
        min_length=1,
        max_length=25,
        validators=[UnicodeUsernameValidator()],
    )
    password = forms.CharField(min_length=8, max_length=128)
    nickname = forms.CharField(min_length=1, max_length=25)
    email = forms.EmailField(max_length=254)
    avatar = forms.ImageField(required=False)

    def clean_username(self):
        return self.cleaned_data["username"].strip()

    def clean_email(self):
        return User.objects.normalize_email(self.cleaned_data["email"]).lower()

    def clean_password(self):
        password = self.cleaned_data["password"]
        candidate = User(username=self.data.get("username", ""), email=self.data.get("email", ""))
        try:
            validate_password(password, user=candidate)
        except ValidationError as error:
            raise forms.ValidationError(error.messages) from error
        return password

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar is None:
            return None
        if avatar.size > settings.MAX_AVATAR_BYTES:
            raise forms.ValidationError("Avatar exceeds the maximum file size.")
        width, height = avatar.image.size
        if width * height > settings.MAX_AVATAR_PIXELS:
            raise forms.ValidationError("Avatar dimensions are too large.")
        extension = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "WEBP": ".webp",
        }.get(avatar.image.format)
        if extension is None:
            raise forms.ValidationError("Avatar must be JPEG, PNG, or WebP.")
        avatar.name = f"{uuid4().hex}{extension}"
        avatar.seek(0)
        return avatar


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=128)


class ResendVerificationForm(forms.Form):
    username = forms.CharField(max_length=150)

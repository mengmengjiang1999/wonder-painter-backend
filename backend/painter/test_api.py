"""Integration tests for the public API."""

import re
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from painter.models import EmailVerification, Profile
from painter.send_email import digest_token

PASSWORD = "Strong_course_pass_123!"


@pytest.fixture(autouse=True)
def isolated_state(settings, tmp_path):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.MEDIA_ROOT = tmp_path / "media"
    cache.clear()


@pytest.fixture
def csrf_client():
    client = Client(enforce_csrf_checks=True)
    token = client.get("/csrf/").json()["csrfToken"]
    return client, token


def post(client, token, path, data=None):
    return client.post(path, data or {}, HTTP_X_CSRFTOKEN=token)


def registration_data(**overrides):
    data = {
        "username": "course_user",
        "password": PASSWORD,
        "nickname": "测试用户",
        "email": "student@example.com",
    }
    data.update(overrides)
    return data


def token_from_latest_email():
    url = re.search(r"https?://\S+", mail.outbox[-1].body).group(0)
    return parse_qs(urlparse(url).query)["token"][0]


@pytest.mark.django_db
def test_registration_verification_session_and_logout(csrf_client):
    client, csrf = csrf_client

    response = post(client, csrf, "/register/", registration_data())

    assert response.status_code == 201
    user = User.objects.get(username="course_user")
    assert not user.is_active
    assert user.check_password(PASSWORD)
    profile = Profile.objects.get(user=user)
    assert profile.nickname == "测试用户"
    assert profile.email_key == "student@example.com"
    token = token_from_latest_email()
    verification = EmailVerification.objects.get(user=user)
    assert verification.token_digest == digest_token(token)
    assert token not in verification.token_digest

    response = post(
        client,
        csrf,
        "/login/",
        {
            "username": user.username,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 401

    response = client.get("/validate/", {"username": user.username, "token": token})
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_active
    assert not EmailVerification.objects.filter(user=user).exists()

    response = post(
        client,
        csrf,
        "/login/",
        {
            "username": user.username,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 200
    assert client.get("/session/").json() == {
        "authenticated": True,
        "username": user.username,
    }

    csrf = client.get("/csrf/").json()["csrfToken"]
    assert post(client, csrf, "/logout/").status_code == 200
    assert client.get("/session/").json() == {"authenticated": False}


@pytest.mark.django_db
def test_csrf_and_http_methods_are_enforced():
    client = Client(enforce_csrf_checks=True)

    assert client.post("/register/", registration_data()).status_code == 403
    assert client.get("/register/").status_code == 405
    assert client.get("/login/").status_code == 405
    assert client.get("/logout/").status_code == 405


@pytest.mark.django_db
def test_registration_rolls_back_when_email_fails(csrf_client, monkeypatch):
    client, csrf = csrf_client

    def fail_to_send(*args, **kwargs):
        raise OSError("SMTP unavailable")

    monkeypatch.setattr("painter.views.send_verification_email", fail_to_send)
    response = post(client, csrf, "/register/", registration_data())

    assert response.status_code == 503
    assert User.objects.count() == 0
    assert Profile.objects.count() == 0
    assert EmailVerification.objects.count() == 0


@pytest.mark.django_db
def test_resend_replaces_the_old_token(csrf_client):
    client, csrf = csrf_client
    assert post(client, csrf, "/register/", registration_data()).status_code == 201
    old_token = token_from_latest_email()

    response = post(client, csrf, "/resend-verification/", {"username": "course_user"})

    assert response.status_code == 200
    new_token = token_from_latest_email()
    assert new_token != old_token
    assert (
        client.get(
            "/validate/",
            {
                "username": "course_user",
                "token": old_token,
            },
        ).status_code
        == 400
    )
    assert (
        client.get(
            "/validate/",
            {
                "username": "course_user",
                "token": new_token,
            },
        ).status_code
        == 200
    )


@pytest.mark.django_db
def test_registration_validates_fields_and_duplicates(csrf_client):
    client, csrf = csrf_client

    assert (
        post(client, csrf, "/register/", registration_data(username="bad name")).status_code == 400
    )
    assert (
        post(client, csrf, "/register/", registration_data(password="password")).status_code == 400
    )
    assert (
        post(client, csrf, "/register/", registration_data(email="not-an-email")).status_code == 400
    )
    assert post(client, csrf, "/register/", registration_data()).status_code == 201
    assert post(client, csrf, "/register/", registration_data()).status_code == 409
    assert (
        post(
            client,
            csrf,
            "/register/",
            registration_data(
                username="another_user",
                email="STUDENT@example.com",
            ),
        ).status_code
        == 409
    )


@pytest.mark.django_db
def test_avatar_is_validated_and_randomly_named(csrf_client):
    client, csrf = csrf_client
    invalid = SimpleUploadedFile("avatar.jpg", b"not an image", content_type="image/jpeg")
    assert post(client, csrf, "/register/", registration_data(avatar=invalid)).status_code == 400

    image_buffer = BytesIO()
    Image.new("RGB", (32, 32), color="blue").save(image_buffer, format="PNG")
    avatar = SimpleUploadedFile(
        "identifying-name.png", image_buffer.getvalue(), content_type="image/png"
    )
    response = post(client, csrf, "/register/", registration_data(avatar=avatar))

    assert response.status_code == 201
    stored_name = Profile.objects.get(user__username="course_user").avatar.name
    assert stored_name.startswith("avatars/")
    assert stored_name.endswith(".png")
    assert "identifying-name" not in stored_name


@pytest.mark.django_db
def test_rate_limit_returns_429(csrf_client):
    client, csrf = csrf_client
    for index in range(10):
        response = post(client, csrf, "/register/", registration_data(username=f"bad name {index}"))
        assert response.status_code == 400

    response = post(client, csrf, "/register/", registration_data(username="another"))

    assert response.status_code == 429
    assert response["Retry-After"] == "3600"


@pytest.mark.django_db
def test_verification_is_single_use_and_rejects_invalid_links(csrf_client):
    client, csrf = csrf_client
    assert post(client, csrf, "/register/", registration_data()).status_code == 201
    token = token_from_latest_email()

    assert client.get("/validate/").status_code == 400
    assert (
        client.get("/validate/", {"username": "course_user", "token": "wrong"}).status_code == 400
    )
    assert client.get("/validate/", {"username": "course_user", "token": token}).status_code == 200
    assert client.get("/validate/", {"username": "course_user", "token": token}).status_code == 400


@pytest.mark.django_db
def test_expired_token_is_deleted(csrf_client):
    client, csrf = csrf_client
    assert post(client, csrf, "/register/", registration_data()).status_code == 201
    token = token_from_latest_email()
    verification = EmailVerification.objects.get(user__username="course_user")
    verification.expires_at = verification.sent_at
    verification.save(update_fields=["expires_at"])

    response = client.get("/validate/", {"username": "course_user", "token": token})

    assert response.status_code == 400
    assert not EmailVerification.objects.filter(pk=verification.pk).exists()

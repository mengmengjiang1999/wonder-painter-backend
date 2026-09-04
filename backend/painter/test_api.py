"""API integration tests for Wonder Painter."""
from datetime import timedelta

import pytest
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.test import Client
from django.utils import timezone

from painter.models import EmailVerifyRecord, User


@pytest.mark.django_db
def test_registration_verification_and_login_flow(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    client = Client()

    response = client.post('/register/', {
        'username': 'course_user',
        'password': 'safe_pass_123',
        'nickname': '测试用户',
        'email': 'student@example.com',
    })

    assert response.status_code == 200
    user = User.objects.get(username='course_user')
    assert user.password != 'safe_pass_123'
    assert check_password('safe_pass_123', user.password)
    assert len(mail.outbox) == 1

    response = client.post('/login/', {
        'username': 'course_user',
        'password': 'safe_pass_123',
    })
    assert response.status_code == 400
    assert response.json()['message'] == 'The user has not been validated.'

    record = EmailVerifyRecord.objects.get(username='course_user')
    response = client.get('/validate/', {
        'username': record.username,
        'code': record.code,
    })
    assert response.status_code == 200

    response = client.post('/login/', {
        'username': 'course_user',
        'password': 'safe_pass_123',
    })
    assert response.status_code == 200


@pytest.mark.django_db
def test_registration_rejects_invalid_and_duplicate_users(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    client = Client()
    valid_data = {
        'username': 'course_user',
        'password': 'safe_pass_123',
        'nickname': '测试用户',
        'email': 'student@example.com',
    }

    assert client.get('/register/').status_code == 400
    assert client.post('/register/', {**valid_data, 'username': 'bad name'}).status_code == 400
    assert client.post('/register/', {**valid_data, 'password': 'short'}).status_code == 400
    assert client.post('/register/', {**valid_data, 'email': 'not-an-email'}).status_code == 400
    assert client.post('/register/', valid_data).status_code == 200
    assert client.post('/register/', valid_data).status_code == 400


@pytest.mark.django_db
def test_login_rejects_unknown_user_and_wrong_password(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    client = Client()

    response = client.post('/login/', {
        'username': 'missing',
        'password': 'safe_pass_123',
    })
    assert response.status_code == 400
    assert response.json()['message'] == 'No such user'

    client.post('/register/', {
        'username': 'course_user',
        'password': 'safe_pass_123',
        'nickname': '测试用户',
        'email': 'student@example.com',
    })
    response = client.post('/login/', {
        'username': 'course_user',
        'password': 'wrong_pass_123',
    })
    assert response.status_code == 400
    assert response.json()['message'] == 'Wrong password'


@pytest.mark.django_db
def test_expired_verification_code_is_rejected(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    client = Client()
    client.post('/register/', {
        'username': 'course_user',
        'password': 'safe_pass_123',
        'nickname': '测试用户',
        'email': 'student@example.com',
    })
    record = EmailVerifyRecord.objects.get(username='course_user')
    record.send_time = timezone.now() - timedelta(hours=settings.CONFIRM_HOURS + 1)
    record.save(update_fields=['send_time'])

    response = client.get('/validate/', {
        'username': record.username,
        'code': record.code,
    })

    assert response.status_code == 400
    assert response.json()['message'] == 'Expired'

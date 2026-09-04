"""HTTP endpoints for registration and session authentication."""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .forms import LoginForm, RegistrationForm, ResendVerificationForm
from .models import EmailVerification, Profile
from .send_email import create_token, digest_token, send_verification_email
from .throttling import rate_limit

LOGGER = logging.getLogger(__name__)


def error_response(form):
    return JsonResponse(
        {"message": "Invalid input", "errors": form.errors.get_json_data()},
        status=400,
    )


@ensure_csrf_cookie
@require_GET
def csrf_token(request):
    """Set a CSRF cookie and return the token for API clients."""
    return JsonResponse({"csrfToken": get_token(request)})


@require_POST
@rate_limit("register", limit=10, window_seconds=3600)
def register(request):
    """Create an inactive user and send an email-verification link."""
    form = RegistrationForm(request.POST, request.FILES)
    if not form.is_valid():
        return error_response(form)

    data = form.cleaned_data
    if User.objects.filter(username__iexact=data["username"]).exists():
        return JsonResponse({"message": "Username or email unavailable"}, status=409)
    if Profile.objects.filter(email_key=data["email"]).exists():
        return JsonResponse({"message": "Username or email unavailable"}, status=409)

    token = create_token()
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                is_active=False,
            )
            Profile.objects.create(
                user=user,
                email_key=data["email"],
                nickname=data["nickname"],
                avatar=data.get("avatar") or "",
            )
            EmailVerification.objects.create(
                user=user,
                token_digest=digest_token(token),
                expires_at=timezone.now() + timedelta(hours=settings.CONFIRM_HOURS),
            )
            send_verification_email(user, token)
    except IntegrityError:
        return JsonResponse({"message": "Username or email unavailable"}, status=409)
    except Exception:
        LOGGER.exception("Registration email could not be sent")
        return JsonResponse({"message": "Verification email unavailable"}, status=503)

    return JsonResponse(
        {"message": "Registration successful; check your email to activate the account."},
        status=201,
    )


@require_POST
@rate_limit("resend-verification", limit=5, window_seconds=3600)
def resend_verification(request):
    """Replace and resend the verification token for an inactive account."""
    form = ResendVerificationForm(request.POST)
    if not form.is_valid():
        return error_response(form)

    user = User.objects.filter(username__iexact=form.cleaned_data["username"]).first()
    if user is None or user.is_active:
        return JsonResponse({"message": "If the account is pending, a new email was sent."})

    token = create_token()
    try:
        with transaction.atomic():
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={
                    "token_digest": digest_token(token),
                    "sent_at": timezone.now(),
                    "expires_at": timezone.now() + timedelta(hours=settings.CONFIRM_HOURS),
                },
            )
            send_verification_email(user, token)
    except Exception:
        LOGGER.exception("Verification email could not be resent")
        return JsonResponse({"message": "Verification email unavailable"}, status=503)
    return JsonResponse({"message": "If the account is pending, a new email was sent."})


@require_POST
@rate_limit("login", limit=20, window_seconds=300)
def login(request):
    """Authenticate a user and establish a Django session."""
    form = LoginForm(request.POST)
    if not form.is_valid():
        return error_response(form)
    user = authenticate(
        request,
        username=form.cleaned_data["username"],
        password=form.cleaned_data["password"],
    )
    if user is None:
        return JsonResponse({"message": "Invalid credentials or inactive account"}, status=401)
    auth_login(request, user)
    return JsonResponse({"message": "Login successful", "username": user.username})


@require_POST
def logout(request):
    """End the current Django session."""
    auth_logout(request)
    return JsonResponse({"message": "Logout successful"})


@require_GET
def session_status(request):
    """Return the current session authentication state."""
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False})
    return JsonResponse({"authenticated": True, "username": request.user.username})


@require_GET
@rate_limit("validate", limit=30, window_seconds=300)
def validate(request):
    """Consume a valid email token and activate its user."""
    username = request.GET.get("username", "")
    token = request.GET.get("token", "")
    if not username or not token:
        return JsonResponse({"message": "Invalid verification link"}, status=400)

    with transaction.atomic():
        verification = (
            EmailVerification.objects.select_for_update()
            .select_related("user")
            .filter(user__username=username, token_digest=digest_token(token))
            .first()
        )
        if verification is None:
            return JsonResponse({"message": "Invalid verification link"}, status=400)
        if verification.expires_at <= timezone.now():
            verification.delete()
            return JsonResponse({"message": "Verification link expired"}, status=400)
        user = verification.user
        user.is_active = True
        user.save(update_fields=["is_active"])
        verification.delete()
    return JsonResponse({"message": "Verification successful"})

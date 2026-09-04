"""Helpers for email verification."""

import hashlib
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def create_token():
    """Return a high-entropy token suitable for an emailed link."""
    return secrets.token_urlsafe(32)


def digest_token(token):
    """Return the non-reversible representation stored in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def send_verification_email(user, token):
    """Send a single-use account verification link."""
    query = urlencode({"username": user.username, "token": token})
    href = f"{settings.APP_BASE_URL}/validate/?{query}"

    subject = "来自Wonder Painter的注册确认邮件"

    text_content = (
        "欢迎注册 Wonder Painter。\n"
        f"请在 {settings.CONFIRM_HOURS} 小时内访问以下链接完成验证：\n{href}"
    )

    html_content = (
        "<p>感谢注册 Wonder Painter。</p>"
        f'<p><a href="{href}" target="_blank" rel="noopener noreferrer">完成邮箱验证</a></p>'
        f"<p>此链接有效期为 {settings.CONFIRM_HOURS} 小时。</p>"
    )

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

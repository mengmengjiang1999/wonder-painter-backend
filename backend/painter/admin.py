from django.contrib import admin

from .models import EmailVerification, Profile

admin.site.register(Profile)
admin.site.register(EmailVerification)

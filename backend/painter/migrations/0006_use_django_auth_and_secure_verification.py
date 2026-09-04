import hashlib
from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def migrate_legacy_users(apps, schema_editor):
    legacy_user_model = apps.get_model('painter', 'User')
    auth_user_model = apps.get_model('auth', 'User')
    profile_model = apps.get_model('painter', 'Profile')
    verification_model = apps.get_model('painter', 'EmailVerification')

    users_by_name = {}
    for legacy_user in legacy_user_model.objects.all().iterator():
        normalized_email = legacy_user.email.strip()[:254]
        auth_user, _ = auth_user_model.objects.update_or_create(
            username=legacy_user.username,
            defaults={
                'email': normalized_email,
                'password': legacy_user.password,
                'is_active': legacy_user.valid,
            },
        )
        avatar_name = str(legacy_user.avatar or '')
        if avatar_name.endswith(('^default.jpg', 'default.jpg')):
            avatar_name = ''
        email_key = normalized_email.lower()
        if profile_model.objects.filter(email_key=email_key).exclude(user=auth_user).exists():
            email_key = f'legacy-{legacy_user.pk}@invalid.local'
        profile_model.objects.update_or_create(
            user=auth_user,
            defaults={
                'email_key': email_key,
                'nickname': legacy_user.nickname,
                'avatar': avatar_name,
            },
        )
        users_by_name[legacy_user.username] = auth_user

    for verification in verification_model.objects.all().iterator():
        auth_user = users_by_name.get(verification.username)
        if auth_user is None or verification.send_type != 1:
            verification.delete()
            continue
        verification.user = auth_user
        verification.token_digest = hashlib.sha256(
            verification.code.encode('utf-8')
        ).hexdigest()
        verification.expires_at = verification.sent_at + timedelta(hours=72)
        verification.save(
            update_fields=['user', 'token_digest', 'expires_at']
        )


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('painter', '0005_secure_password_and_timestamp_defaults'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_key', models.CharField(editable=False, max_length=254, unique=True)),
                ('nickname', models.CharField(max_length=25)),
                ('avatar', models.ImageField(blank=True, upload_to='avatars')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RenameModel(
            old_name='EmailVerifyRecord',
            new_name='EmailVerification',
        ),
        migrations.RenameField(
            model_name='emailverification',
            old_name='send_time',
            new_name='sent_at',
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='sent_at',
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AddField(
            model_name='emailverification',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='email_verification', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='emailverification',
            name='token_digest',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='emailverification',
            name='expires_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(migrate_legacy_users, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='emailverification',
            name='code',
        ),
        migrations.RemoveField(
            model_name='emailverification',
            name='email',
        ),
        migrations.RemoveField(
            model_name='emailverification',
            name='send_type',
        ),
        migrations.RemoveField(
            model_name='emailverification',
            name='username',
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='expires_at',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='token_digest',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='email_verification', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='User',
        ),
    ]

from django.db import migrations, models
from django.contrib.auth.hashers import identify_hasher, make_password
from django.utils import timezone


def hash_existing_passwords(apps, schema_editor):
    """Convert passwords created by the 2019 prototype to Django hashes."""
    user_model = apps.get_model('painter', 'User')
    for user in user_model.objects.all().iterator():
        try:
            identify_hasher(user.password)
        except ValueError:
            user.password = make_password(user.password)
            user.save(update_fields=['password'])


class Migration(migrations.Migration):

    dependencies = [
        ('painter', '0004_emailverifyrecord'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=128),
        ),
        migrations.RunPython(hash_existing_passwords, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=25, unique=True),
        ),
        migrations.AlterField(
            model_name='emailverifyrecord',
            name='send_time',
            field=models.DateTimeField(default=timezone.now, verbose_name='发送时间'),
        ),
    ]

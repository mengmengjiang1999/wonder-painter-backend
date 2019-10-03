from django.db import models

# Create your models here.

class User(models.Model):
    username = models.CharField(max_length = 25)
    password = models.CharField(max_length = 25)
    nickname = models.CharField(max_length = 25)
    email = models.CharField(max_length = 256)
    avatar = models.ImageField(upload_to = 'avatars')

    def __str__(self):
        return self.username

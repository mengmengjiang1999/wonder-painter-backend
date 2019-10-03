from django.db import models
from datetime import datetime

# Create your models here.

class User(models.Model):
    """
    用户类，用于存储用户信息。
    username：用户名
    password：密码
    nickname：昵称
    email：邮箱
    avatar：头像
    valid：是否进行邮箱验证
    """
    username = models.CharField(max_length = 25)
    password = models.CharField(max_length = 25)
    nickname = models.CharField(max_length = 25)
    email = models.CharField(max_length = 256)
    avatar = models.ImageField(upload_to = 'avatars')
    valid = models.BooleanField(default = False)

    def __str__(self):
        return self.username


class EmailVerifyRecord(models.Model):
    """
    邮箱验证类，用于进行邮箱验证。
    username：进行邮箱验证的用户名
    code：验证码
    email：邮箱
    send_type：验证码类型，1表示验证邮箱，2表示找回密码
    send_time：验证码发送时间
    """
    username = models.CharField(max_length=25)
    code = models.CharField(max_length=20, verbose_name=u"验证码")
    email = models.EmailField(max_length=256, verbose_name=u"邮箱")
    # 包含注册验证和找回验证
    send_type = models.IntegerField()
    send_time = models.DateTimeField(verbose_name=u"发送时间", default=datetime.now())
    def __str__(self):
        return '{0}({1})'.format(self.code, self.email)

" views.py "
from shutil import copyfile
from datetime import datetime, timezone
import os
import re
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from painter.models import User, EmailVerifyRecord
from .send_email import random_str, send_email

# Create your views here.

NAME_MAX_LEN = 25


@csrf_exempt
def register(request):
    """
    用于注册，使用POST，参数如下：
    username: 用户名，需要唯一，仅允许大小写字母、下划线和数字，不长于25位
    password: 密码，长度不低于8位，不长于25位
    email: 邮箱，需要验证之后才能使用
    nickname: 昵称，可以与其他人重名，支持中文名
    avatar: 头像图片，可以不上传，此时将使用默认头像
    """
    if request.method != 'POST':
        return JsonResponse({'message': 'Not POST'}, status=400)
    if request.POST.get('username') is None:
        return JsonResponse({'message': 'No username'}, status=400)
    if request.POST.get('password') is None:
        return JsonResponse({'message': 'No password'}, status=400)
    if request.POST.get('nickname') is None:
        return JsonResponse({'message': 'No nickname'}, status=400)
    if request.POST.get('email') is None:
        return JsonResponse({'message': 'No email'}, status=400)
    username = request.POST.get('username')
    password = request.POST.get('password')
    nickname = request.POST.get('nickname')
    email = request.POST.get('email')
    if len(username) > NAME_MAX_LEN or not username.replace('_', '0').isalnum():
        return JsonResponse({'message': 'Username format error'}, status=400)
    if len(password) > NAME_MAX_LEN or not password.replace('_', '0').isalnum():
        return JsonResponse({'message': 'Password format error'}, status=400)
    if len(nickname) > NAME_MAX_LEN:
        return JsonResponse({'message': 'Nickname format error'}, status=400)
    if not re.match(r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$', email):
        return JsonResponse({'message': 'Email format error'}, status=400)
    if len(User.objects.filter(username=username)) != 0:
        return JsonResponse({'message': 'Repeat username'}, status=400)
    if request.FILES.get('avatar') is None:
        copyfile(os.path.join(settings.AVATAR_ROOT, '^default.jpg'), os.path.join(settings.AVATAR_ROOT, username+'.jpg'))
        User.objects.create(username=username, password=password, nickname=nickname, email=email)
    else:
        avatar = request.FILES.get('avatar')
        avatar.name = username + '.jpg'
        User.objects.create(username=username, password=password, nickname=nickname, email=email, avatar=avatar)

    code = random_str(20)
    send_email(email, username, code)
    EmailVerifyRecord.objects.create(username=username, code=code, email=email, send_type=1)
    return JsonResponse({'message': 'Register successfully, please verify your account by email in 72 hours.'}, status=200)


@csrf_exempt
def login(request):
    """
    用于登录，使用POST，参数如下：
    username: 用户名，需要唯一，仅允许大小写字母、下划线和数字，不长于25位
    password: 密码，长度不低于8位，不长于25位
    TODO
    """
    if request.method != 'POST':
        return JsonResponse({'message': 'Not POST'}, status=400)
    if request.POST.get('username') is None:
        return JsonResponse({'message': 'No username'}, status=400)
    if request.POST.get('password') is None:
        return JsonResponse({'message': 'No password'}, status=400)
    username = request.POST.get('username')
    password = request.POST.get('password')
    items = User.objects.filter(username=username)
    if len(items) == 0:
        return JsonResponse({'message': 'No such user'}, status=400)
    item = items[0]
    if item.password != password:
        return JsonResponse({'message': 'Wrong password'}, status=400)
    if not item.valid:
        return JsonResponse({'message': 'The user has not been validated.'}, status=400)
    return JsonResponse({'message': 'Login successfully'}, status=200)


def validate(request):
    """
    用于验证邮箱，使用GET，参数如下：
    username：验证者用户名
    code：验证码
    TODO
    """
    if request.method != 'GET':
        return JsonResponse({'message': 'Not GET'}, status=400)
    if request.GET.get('username') is None:
        return JsonResponse({'message': 'No username'}, status=400)
    if request.GET.get('code') is None:
        return JsonResponse({'message': 'No code'}, status=400)
    username = request.GET.get('username')
    code = request.GET.get('code')
    items = EmailVerifyRecord.objects.filter(username=username, code=code, send_type=1)
    if len(items) == 0:
        return JsonResponse({'message': 'Verify Failed.'}, status=400)
    item = items[0]
    if (datetime.now(timezone.utc) - item.send_time).seconds / 60 / 60 > settings.CONFIRM_HOURS:
        return JsonResponse({'message': 'Expired'}, status=400)
    user = User.objects.filter(username=username)[0]
    user.valid = True
    user.save()
    item.delete()
    return JsonResponse({'message': 'Verify Successfully.'}, status=200)

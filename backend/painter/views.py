from django.shortcuts import render
from django.http import HttpResponse
from painter.models import User
from django.views.decorators.csrf import csrf_exempt
from shutil import copyfile
from django.conf import settings
import os
import re

# Create your views here.

NAME_MAX_LEN = 25


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return HttpResponse('Not POST', status = 400)
    if request.POST.get('username') == None:
        return HttpResponse('No username', status = 400)
    if request.POST.get('password') == None:
        return HttpResponse('No password', status = 400)
    if request.POST.get('nickname') == None:
        return HttpResponse('No nickname', status = 400)
    if request.POST.get('email') == None:
        return HttpResponse('No email', status = 400)
    username = request.POST.get('username')
    password = request.POST.get('password')
    nickname = request.POST.get('nickname')
    email = request.POST.get('email')
    if len(username) > NAME_MAX_LEN or username.replace('_', '0').isalnum() == False:
        return HttpResponse('Username format error', status = 400)
    if len(password) > NAME_MAX_LEN or password.replace('_', '0').isalnum() == False:
        return HttpResponse('Password format error', status = 400)
    if len(nickname) > NAME_MAX_LEN:
        return HttpResponse('Nickname format error', status = 400)
    if re.match(r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$', email) == False:
        return HttpResponse('Email format error', status = 400)
    if len(User.objects.filter(username = username)) != 0:
        return HttpResponse('Repeat username', status = 400)
    if request.FILES.get('avatar') == None:
        copyfile(os.path.join(settings.AVATAR_ROOT,'^default.jpg'),os.path.join(settings.AVATAR_ROOT,username+'.jpg'))
        User.objects.create(username = username, password = password, nickname = nickname, email = email)
    else:
        avatar = request.FILES.get('avatar')
        avatar.name = username + '.jpg'
        User.objects.create(username = username, password = password, nickname = nickname, email = email, avatar = avatar)
    return HttpResponse('Register successfully', status = 200)


def login(request):
    if request.method != 'POST':
        return HttpResponse('Not POST', status = 400)

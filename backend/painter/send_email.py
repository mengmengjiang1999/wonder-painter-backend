"""Helpers for email verification."""
import secrets
import string
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def random_str(randomlength=20):
    ''' 生成一个随机的字符串，默认长度为20 '''
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(randomlength))

def send_email(email, username, code):
    ''' 发送邮件，邮箱为email，验证者用户名为username，验证码为code '''
    query = urlencode({'username': username, 'code': code})
    href = '{0}/validate/?{1}'.format(settings.APP_BASE_URL, query)

    subject = '来自Wonder Painter的注册确认邮件'

    text_content = '''欢迎注册Wonder Painter
                    如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请手动进入 {0} 进行验证'''.format(href)

    html_content = '''
                        <p>感谢注册<a href="{0}" target=blank>{0}</a></p>
                        <p>请点击站点链接完成注册确认！</p>
                        <p>此链接有效期为72小时！</p>
                        '''.format(href)

    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

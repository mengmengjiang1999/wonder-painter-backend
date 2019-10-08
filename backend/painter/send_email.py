" For sending email to verify. "
from random import Random # 用于生成随机码
from django.core.mail import send_mail # 发送邮件模块
from django.conf import settings  # setting.py添加的的配置信息
from .models import EmailVerifyRecord # 邮箱验证model

def random_str(randomlength=20):
    ''' 生成一个随机的字符串，默认长度为20 '''
    ret = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        ret += chars[random.randint(0, length)]
    return ret

def send_email(email, username, code):
    ''' 发送邮件，邮箱为email，验证者用户名为username，验证码为code '''
    from django.core.mail import EmailMultiAlternatives
    href = 'http://{0}/validate/?username={1}&code={2}'.format('127.0.0.1:8080', username, code)

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

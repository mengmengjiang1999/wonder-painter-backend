# Wonder Painter Backend

Wonder Painter 是 2019 年秋季软件工程课程的团队项目。本仓库保存其 Django 后端原型，提供用户注册、邮箱验证、登录和头像上传功能。

> 课程归档说明：这是一个教学原型，不是经过安全审计的生产系统。

## 团队分工与贡献边界

本仓库的 Git 历史只能核实后端部分的贡献：

| 成员/记录 | 可核验贡献 |
| --- | --- |
| `yangyr17` / `dylanyang17` | Django 项目初始化，注册与登录，头像上传，邮箱验证，测试与早期 CI |
| 其他课程组员 | 未在本仓库的提交历史中留下可归属记录；前端、设计和产品分工待原团队成员补充 |

上表仅根据仓库历史整理，不对历史中无法核实的工作做归属推断。

## 技术栈

- Python 3.9+
- Django 4.2 LTS
- SQLite（默认开发数据库）
- pytest + pytest-django
- Gunicorn / Docker

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
```

Django 不会自动读取 `.env` 文件。在本地开发时，可将其中的变量导入当前 shell，或在 IDE/运行平台中配置同名环境变量。默认邮件后端会把验证邮件输出到终端，无需真实 SMTP 账号。

```bash
python backend/manage.py migrate
python backend/manage.py runserver
```

服务默认访问地址为 `http://127.0.0.1:8000`。

## Docker 部署

```bash
docker build -t wonder-painter-backend .
docker run --rm -p 8000:8000 \
  -e DJANGO_SECRET_KEY = 'REMOVED_ROTATE_SMTP_CREDENTIAL' \
  -e DJANGO_DEBUG=false \
  -e DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1' \
  wonder-painter-backend
```

容器启动时会自动执行数据库迁移。演示以外的部署应将 SQLite 文件所在目录挂载到持久化存储，或改用外部数据库。若需发送真实验证邮件，请在部署平台配置 `EMAIL_HOST` 、`EMAIL_PORT`、`EMAIL_HOST_USER`、`EMAIL_HOST_PASSWORD` 和 `EMAIL_USE_TLS`；不要将密码写入仓库。

## API

请求使用表单编码；上传头像时使用 `multipart/form-data`。响应均为 JSON：`{"message": "..."}`。

### `POST /register/`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `username` | 是 | 唯一；最长 25 位；字母、数字和下划线 |
| `password` | 是 | 8–25 位；字母、数字和下划线；服务端以 Django 密码哈希存储 |
| `nickname` | 是 | 最长 25 位，可以重名 |
| `email` | 是 | 用于接收验证链接 |
| `avatar` | 否 | 头像文件；未上传时使用默认头像 |

成功返回 HTTP 200；方法、字段、格式或用户名重复错误返回 HTTP 400。

### `GET /validate/`

| 查询参数 | 说明 |
| --- | --- |
| `username` | 待验证用户名 |
| `code` | 注册邮件中的验证码 |

验证链接默认 72 小时有效。成功返回 HTTP 200，无效或过期返回 HTTP 400。

### `POST /login/`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `username` | 是 | 已注册用户名 |
| `password` | 是 | 用户密码 |

只有完成邮箱验证的用户可登录。成功返回 HTTP 200，其他情况返回 HTTP 400。

## 配置

| 环境变量 | 默认值 | 用途 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | 仅开发环境有不安全默认值 | Django 签名密钥；生产环境必填 |
| `DJANGO_DEBUG` | `true` | 是否开启调试模式 |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | 逗号分隔的主机名 |
| `APP_BASE_URL` | `http://127.0.0.1:8000` | 邮件验证链接的站点根地址 |
| `EMAIL_BACKEND` | console backend | Django 邮件后端 |
| `EMAIL_HOST*` | 见 `.env.example` | SMTP 连接配置 |

## 测试

```bash
pytest --cov=backend/painter --cov-report=term-missing
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
```

测试覆盖注册、密码哈希、邮件发送、验证码、验证过期、登录、重复用户和常见输入错误。GitHub Actions 会在每次 push 和 pull request 时重复上述检查。

2026-09-04 的本地验证结果（Python 3.9.6 / Django 4.2.30）：4 项测试全部通过，核心业务代码行覆盖率 86%，Django 系统检查通过，没有未生成的模型迁移。

## 安全与数据

- 仓库不再跟踪运行数据库、用户上传、覆盖率文件、缓存和编辑器交换文件。
- 密码使用 Django 密码哈希存储，验证码使用密码学安全的随机源生成。
- 早期历史曾包含开发密钥和 SMTP 凭据。即使当前版本已移除，原凭据仍应视为已泄露并在服务提供方处轮换。

## 项目状态

课程项目已结课，本仓库作为学习与作品集档案保留。未声明开源许可证，仓库公开不代表授予复制、修改或再分发权限。

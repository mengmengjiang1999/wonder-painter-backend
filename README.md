# Wonder Painter Backend

Wonder Painter 是 2019 年秋季软件工程课程的团队项目。本仓库保存其 Django 后端，提供用户注册、邮箱验证、会话登录和头像上传 API。

> 课程归档说明：这是一个教学项目，不是经过独立安全审计的生产服务。

## 团队分工与贡献边界

本仓库的 Git 历史只能核实后端部分的贡献：

| 成员/记录 | 可核验贡献 |
| --- | --- |
| `yangyr17` / `dylanyang17` | Django 项目初始化，注册与登录，头像上传，邮箱验证，测试与早期 CI |
| 其他课程组员 | 未在本仓库提交历史中留下可归属记录；前端、设计和产品分工待原团队成员补充 |

上表仅根据仓库历史整理，不对无法核实的工作做归属推断。公开仓库前还应取得课程团队同意，并由原成员补充准确分工。

## 技术栈

- Python 3.10+（Docker 使用 Python 3.12）
- Django 5.2 LTS
- SQLite（默认开发和单实例演示数据库）
- pytest、pytest-django、Ruff
- Gunicorn、WhiteNoise、Docker

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
cp .env.example .env
set -a; source .env; set +a
python backend/manage.py migrate
python backend/manage.py runserver
```

Django 不会自动读取 `.env`；上面的命令只适用于兼容 POSIX shell 的本地开发环境，也可以在 IDE 中配置同名变量。默认邮件后端把验证邮件输出到终端，不需要 SMTP 账号。服务地址为 `http://127.0.0.1:8000`。

### 本地 SMTP 凭据

仅在需要真实发信时，编辑项目根目录的 `.env`，填写 `EMAIL_HOST`、`EMAIL_HOST_USER`、`EMAIL_HOST_PASSWORD` 和 `DEFAULT_FROM_EMAIL`，并设置 `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`。密码使用邮箱服务商新生成的 SMTP 授权码；不要复用历史提交中出现过的值。按服务商要求设置端口和 TLS。

执行 `chmod 600 .env` 限制本地访问，再用上面的 `set -a; source .env; set +a` 加载配置并重启服务。若值包含 shell 特殊字符，用单引号包住值（值本身包含单引号时须正确转义）。`.env` 和 `.env.*` 本地配置均被 Git 忽略，只有不含凭据的 `.env.example` 可提交；Docker 构建也排除这些本地配置。不要覆盖已有 `.env`，不要把真实密码写进示例、命令行或日志。

`requirements.lock` 固定生产依赖，`requirements-dev.lock` 额外固定测试与格式检查工具；`requirements*.txt` 保存允许升级的版本范围。

## Docker 部署

先构建镜像并单独执行迁移，再启动服务。将迁移作为独立步骤可避免多个应用副本同时修改数据库：

```bash
docker build -t wonder-painter-backend .

docker run --rm \
  -v wonder-painter-data:/data \
  -e DJANGO_SECRET_KEY='replace-with-a-long-random-value' \
  -e DJANGO_DEBUG=false \
  -e DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1' \
  wonder-painter-backend python manage.py migrate

docker run --rm -p 8000:8000 \
  -v wonder-painter-data:/data \
  -e DJANGO_SECRET_KEY='replace-with-the-same-long-random-value' \
  -e DJANGO_DEBUG=false \
  -e DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1' \
  -e DJANGO_SESSION_COOKIE_SECURE=false \
  -e DJANGO_CSRF_COOKIE_SECURE=false \
  wonder-painter-backend
```

上例的两个 `*_COOKIE_SECURE=false` 仅用于本机 HTTP 演示。公网部署必须使用 HTTPS，并启用安全 Cookie、HTTPS 重定向和 HSTS；只有在可信反向代理会覆盖该请求头时才启用 `DJANGO_TRUST_PROXY_HEADERS`。SQLite 适合单实例演示，多实例部署应改用外部数据库。生产环境还应：

- 设置真实的 `APP_BASE_URL`、`DJANGO_CSRF_TRUSTED_ORIGINS` 和 SMTP 参数；
- 由对象存储或反向代理提供用户上传文件，并限制访问权限；
- 在网关提供共享限流，因为应用内置的内存限流按进程生效；
- 在发布阶段只执行一次数据库迁移，并备份持久化数据。

## API 与 CSRF

除验证链接外，API 使用表单编码；头像上传使用 `multipart/form-data`。写请求受 Django CSRF 保护：客户端先请求 `GET /csrf/`，保存 `csrftoken` Cookie，再在 POST 请求中发送同源 Cookie 和 `X-CSRFToken` 请求头。

| 方法与路径 | 参数 | 成功响应 | 用途 |
| --- | --- | --- | --- |
| `GET /csrf/` | 无 | `200` | 设置 CSRF Cookie，并返回 `csrfToken` |
| `POST /register/` | `username`、`password`、`nickname`、`email`，可选 `avatar` | `201` | 创建未激活账户并发送验证邮件 |
| `POST /resend-verification/` | `username` | `200` | 为待验证账户替换并重发验证令牌 |
| `GET /validate/` | 查询参数 `username`、`token` | `200` | 消耗一次性令牌并激活账户 |
| `POST /login/` | `username`、`password` | `200` | 登录并建立 Django Session |
| `GET /session/` | 无 | `200` | 查询当前会话状态 |
| `POST /logout/` | 无 | `200` | 注销当前会话 |

用户名最长 25 个字符并遵循 Django 用户名规则。密码最长 128 个字符，且必须通过 Django 的长度、常见密码、纯数字和用户属性相似性检查。昵称最长 25 个字符。头像限 JPEG、PNG 或 WebP，默认最大 5 MiB、1600 万像素；服务端使用随机文件名，未上传时不引用外部默认图片。

注册验证令牌默认 72 小时有效，只保存 SHA-256 摘要且只能使用一次。重复用户名或邮箱返回 `409`，输入错误返回 `400`，认证失败返回 `401`，限流返回 `429`，邮件服务不可用返回 `503`。重发接口对不存在和已激活用户使用相同响应，避免账户枚举。

## 配置

完整示例见 [`.env.example`](.env.example)。主要变量如下：

| 环境变量 | 默认值 | 用途 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | 仅调试模式临时生成 | Django 签名密钥；生产必填且应由密钥服务注入 |
| `DJANGO_DEBUG` | `true` | 调试模式 |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | 逗号分隔的主机名 |
| `DJANGO_DB_PATH` | `backend/db.sqlite3` | SQLite 文件位置 |
| `APP_BASE_URL` | `http://127.0.0.1:8000` | 邮件验证链接的站点根地址 |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 空 | HTTPS 来源列表，逗号分隔 |
| `EMAIL_BACKEND` / `EMAIL_*` | console backend | 邮件后端、SMTP 和超时配置 |
| `MAX_AVATAR_BYTES` / `MAX_AVATAR_PIXELS` | 5 MiB / 1600 万 | 上传限制 |

安全相关变量及示例值均列在 `.env.example`。HSTS 一旦被浏览器记住不易撤回，确认全站 HTTPS 后再逐步增大其时长。

## 测试与质量检查

```bash
pytest --cov=backend/painter --cov-report=term-missing
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
ruff check backend
ruff format --check backend
```

测试覆盖注册与事务回滚、密码哈希、邮件发送和重发、令牌过期与一次性消费、CSRF、会话登录与注销、重复身份、限流以及头像校验。2026-09-04 在 Python 3.12.14 / Django 5.2.17 下，本地 9 项测试全部通过，核心业务代码行覆盖率 93%，系统检查和迁移检查通过。GitHub Actions 在 Python 3.10 与 3.12 上重复测试，并执行生产部署检查和 Ruff 检查；Dependabot 每周检查 Python、Actions 与 Docker 依赖更新。

## 安全、历史凭据与数据

- 仓库不跟踪运行数据库、用户上传、覆盖率文件、缓存、虚拟环境或编辑器交换文件。
- 密码由 Django 认证系统哈希存储；邮箱验证令牌使用密码学安全随机源，数据库仅保存摘要。
- 早期 Git 历史曾包含开发密钥和 SMTP 凭据。2026-09-15 再次核查发现旧提交仍有 SMTP 密码，本次针对该密码清理分支历史。任何曾提交的凭据都必须视为已泄露，并在对应服务提供方撤销或轮换；改写 Git 历史不能使已泄露凭据重新安全。旧克隆、Fork、PR 引用及平台缓存可能仍保存旧提交；历史更新后应重新克隆，避免把旧历史推回远端。
- 漏洞报告方式和响应范围见 [`SECURITY.md`](SECURITY.md)。

## 项目状态与许可证

课程项目已结课，本仓库作为学习与作品集档案保留。当前未声明开源许可证；公开可见不代表授予复制、修改或再分发权限。团队确认授权范围后，再选择并添加合适许可证。

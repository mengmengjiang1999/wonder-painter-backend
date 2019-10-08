# 后端

## 邮箱

```
removed@example.com
```

邮箱手机号暂时留 yangyr17 的手机。

## API

### 概览

```
register/ : 注册
login/ : 登录
validate/ : 用于邮箱验证
```

### 注册

```
register/
POST方式，参数如下：

username: 用户名，需要唯一，仅允许大小写字母、下划线和数字，不长于25位
password: 密码，长度不低于8位，不长于25位
email: 邮箱，需要验证之后才能使用
nickname: 昵称，可以与其他人重名，支持中文名
avatar: 头像图片，可以不上传，此时将使用默认头像
```

## 数据库

### User 类

TODO

```
username: 用户名
password: 密码
email: 邮箱
valid: 邮箱是否验证
nickname: 昵称
avatar: 头像

```

### Email 类

TODO

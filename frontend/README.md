# 酒店管理系统前端

本目录是按照 `docs/酒店管理系统对接规范.md` 实现的真实接口前端。

## 文件说明

```text
frontend/
  index.html
  styles.css
  app.js
  assets/
    hotel.jpg
  README.md
```

## 运行方式

请从 FastAPI 后端打开页面，保证前端与 `/api/v1` 接口同源：

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

然后访问：

```text
http://127.0.0.1:8000/
```

## 接口说明

前端所有请求都会发往：

```text
/api/v1
```

登录成功后，前端会保存 `accessToken`，后续请求会附带：

```http
Authorization: Bearer <accessToken>
Content-Type: application/json
```

## 开发账号

开发数据库初始化后可使用：

| 账号 | 密码 | 角色 | 状态 |
| --- | --- | --- | --- |
| `admin01` | `123456` | 管理员 | 已启用 |
| `front01` | `123456` | 前台工作人员 | 已启用 |
| `cleaner01` | `123456` | 保洁员 | 待审核 |
| `auditor01` | `123456` | 审计员 | 已启用 |

`cleaner01` 当前是 `待审核`，用于验证未启用账号不能登录。

## 已覆盖页面

- 登录与账号注册
- 账号审核
- 客户与折扣管理
- 客房类型与客房管理
- 预定管理
- 入住与结账
- 清扫任务
- 操作审计
- 前端对接任务清单

## 已按规范实现的点

- API 基准路径为 `/api/v1`。
- JSON 字段使用 lowerCamelCase，例如 `customerId`、`roomTypeId`、`roomStatus`。
- 统一响应格式为 `{ code, message, data, requestId }`。
- 状态枚举使用规范值，不额外自造状态。
- 金额字段按字符串保存和两位小数显示。
- 时间字段使用 ISO 8601 形式，带 `+08:00`。
- 未登录只能访问登录和注册。
- 登录后按账号角色显示菜单。
- 页面数据、表单提交和操作按钮均请求真实后端接口。

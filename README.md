# DataBaseTask

酒店管理系统课程项目，包含 MySQL 数据库脚本、FastAPI 后端和原生 HTML/CSS/JavaScript 前端。后端同时提供 `/api/v1` 接口和前端静态页面，因此只需要启动一个服务。

## 项目结构

```text
DataBaseTask/
  backend/       FastAPI 后端、测试和本地初始化脚本
  frontend/      通过真实 /api/v1 接口访问后端的前端页面
  HotelSys/      正式建表、种子数据、索引、视图、存储过程和触发器 SQL
  docs/          需求和前后端接口对接规范
  README.md      项目统一搭建与协作说明
```

## 技术栈

- Python 3.9+
- FastAPI、SQLAlchemy、PyMySQL
- MySQL 8.0+
- 原生 HTML、CSS、JavaScript
- JWT Bearer Token 鉴权

## 从零开始搭建

以下命令以 Windows PowerShell 为例。请先安装：

1. Git
2. Miniconda 或 Anaconda
3. MySQL 8.0，并确保 MySQL 服务已启动

### 1. 克隆仓库

```powershell
cd E:\
git clone https://github.com/Melon1234123/DataBaseTask.git
cd E:\DataBaseTask
```

已有仓库时更新代码：

```powershell
cd E:\DataBaseTask
git pull --ff-only
```

### 2. 创建 Python 环境

第一次搭建时创建环境：

```powershell
conda create -n bci python=3.9 -y
conda activate bci
cd E:\DataBaseTask\backend
python -m pip install -r requirements.txt
```

以后只需要运行：

```powershell
conda activate bci
```

### 3. 配置本机数据库密码

每个协作者都使用自己的 MySQL 账号和密码，不要把真实密码发给其他人，也不要写进 README、代码或 `.env.example`。

```powershell
cd E:\DataBaseTask\backend
python scripts\configure_env.py
```

按提示输入：

```text
MySQL host [127.0.0.1]:
MySQL port [3306]:
Database name [HotelSys]:
MySQL user [root]:
MySQL password:
```

脚本会生成本机专用的 `backend/.env`，并自动处理密码中的 `@`、`#`、`:` 等特殊字符。`.env` 已被 Git 忽略，不会上传到 GitHub。

检查是否被正确忽略：

```powershell
cd E:\DataBaseTask
git status --short --ignored
```

输出中出现 `!! backend/.env` 是正常的。

### 4. 初始化开发数据库

第一次运行推荐使用开发初始化脚本：

```powershell
cd E:\DataBaseTask\backend
python scripts\init_dev_db.py
```

该脚本会根据 `.env` 连接 MySQL，创建 `HotelSys`、业务表、视图、存储过程、触发器和演示数据。

开发账号如下，密码均为 `123456`：

| 账号 | 角色 | 初始状态 |
| --- | --- | --- |
| `admin01` | 管理员 | 已启用 |
| `front01` | 前台工作人员 | 已启用 |
| `cleaner01` | 保洁员 | 待审核 |
| `auditor01` | 审计员 | 已启用 |

`cleaner01` 需要管理员审核为“已启用”后才能登录。

### 5. 启动网页和后端

```powershell
conda activate bci
cd E:\DataBaseTask\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

看到以下信息表示启动成功：

```text
Uvicorn running on http://127.0.0.1:8000
```

启动后不要关闭这个 PowerShell 窗口。停止服务时按 `Ctrl + C`。

### 6. 打开并验证

- 系统页面：http://127.0.0.1:8000/
- 健康检查：http://127.0.0.1:8000/health
- API 文档：http://127.0.0.1:8000/docs
- OpenAPI JSON：http://127.0.0.1:8000/openapi.json

`/health` 返回的数据库状态应为：

```json
{
  "data": {
    "status": "ok",
    "database": {
      "status": "ok"
    }
  }
}
```

浏览器中的 `localhost:8000` 和 `127.0.0.1:8000` 属于不同来源，登录状态不共享。建议团队统一使用 `http://127.0.0.1:8000/`。

## 使用正式数据库 SQL

需要与数据库组提交的正式结构联调时，按以下顺序执行 `HotelSys/` 中的脚本。`mysql.exe` 路径请按本机安装位置修改。

```powershell
cd E:\DataBaseTask
$mysql = "E:\mysql\bin\mysql.exe"

& $mysql -u root -p --force -e "SOURCE E:/DataBaseTask/HotelSys/Schema.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/seed.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/Index.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/Views.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/Procedures.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/triggers.sql"
```

正式 `seed.sql` 主要提供字典和基础数据，不一定包含登录账号。需要快速联调登录和业务流程时，使用 `backend/scripts/init_dev_db.py` 更方便。

## 前后端如何工作

```text
浏览器
  ├─ GET /                 -> FastAPI 返回 frontend/ 页面
  └─ /api/v1/*             -> FastAPI 路由和权限校验
                                  |
                                  v
                             MySQL HotelSys
```

- FastAPI 监听 `127.0.0.1:8000`。
- 前端通过同源地址 `/api/v1` 请求真实后端，不需要单独启动前端服务器。
- 登录成功后前端保存 JWT，后续请求携带 `Authorization: Bearer <token>`。
- 后端根据账号角色执行权限校验，并通过 SQLAlchemy/PyMySQL 访问 MySQL。

## 角色权限

| 模块 | 管理员 | 前台工作人员 | 保洁员 | 审计员 |
| --- | --- | --- | --- | --- |
| 账号管理 | 查询、修改、审核、停用 | 注册 | 无 | 无 |
| 客户管理 | 读写、修改折扣 | 读写 | 无 | 只读 |
| 房型和客房 | 读写 | 查询 | 查询 | 查询 |
| 预定、入住、换房、结账 | 读写 | 读写 | 无 | 只读 |
| 清扫任务 | 查询、分配 | 查询 | 查询并处理自己的任务 | 查询 |
| 操作审计 | 查询 | 无 | 无 | 查询 |

只有 `ApprovalStatus = 已启用` 的账号可以登录。

## 后端分层

```text
backend/
  app/
    main.py          FastAPI 入口、路由注册和前端静态文件挂载
    core/            配置、数据库连接、鉴权、权限和统一响应
    schemas/         Pydantic 请求模型
    repositories/    SQL 查询、视图和存储过程调用
    services/        业务规则和事务
    routers/         /api/v1 接口路由
  scripts/           本地配置和开发数据库初始化
  tests/             API 契约测试
```

强一致业务优先调用数据库存储过程：

- `sp_create_reservation`
- `sp_check_in`
- `sp_checkout`
- `sp_start_cleaning`
- `sp_finish_cleaning`

统一响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "requestId": "req-..."
}
```

## 测试

```powershell
conda activate bci
cd E:\DataBaseTask\backend
python -m pytest
```

## 常见问题

### `/health` 显示数据库 `unavailable`

1. 确认 MySQL 服务已经启动。
2. 重新运行 `python scripts\configure_env.py`。
3. 检查数据库 host、端口、用户名、密码和数据库名。
4. 确认 MySQL 用户有创建和访问 `HotelSys` 的权限。

### 端口 8000 被占用

```powershell
Get-NetTCPConnection -LocalPort 8000
Stop-Process -Id <PID>
```

也可以换一个端口：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### 已登录但页面状态不正确

1. 固定使用 `http://127.0.0.1:8000/`。
2. 按 `Ctrl + F5` 强制刷新。
3. 退出后重新登录。

### 新账号不能登录

新注册账号默认为“待审核”，需要管理员进入账号审核页面将其改为“已启用”。

## 协作流程

开始工作前：

```powershell
cd E:\DataBaseTask
git pull --ff-only
```

提交前：

```powershell
conda activate bci
cd E:\DataBaseTask\backend
python -m pytest

cd E:\DataBaseTask
git status --short --ignored
```

确认 `backend/.env` 没有进入暂存区，然后只添加本次修改：

```powershell
git add <本次修改的文件>
git commit -m "说明本次修改"
git push origin main
```

如果不小心暂存了 `.env`：

```powershell
git restore --staged backend/.env
```

# HotelSys Backend

FastAPI 后端实现，对接 `docs/酒店管理系统对接规范.md` 中定义的 `/api/v1` 接口，并连接 MySQL `HotelSys`。

## 本地启动

```powershell
conda activate bci
cd E:\DataBaseTask\backend
python -m pip install -r requirements.txt
python scripts\configure_env.py
python scripts\init_dev_db.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## 本地密码配置

真实数据库密码只放在本机 `backend/.env`，不要提交到 GitHub。

推荐使用：

```powershell
python scripts\configure_env.py
```

脚本会提示输入 MySQL host、端口、用户名、密码和数据库名，然后自动生成 `.env`。如果密码包含 `@` 等 URL 特殊字符，脚本会自动编码。

`.env.example` 只保留占位示例；`.env` 已在根目录 `.gitignore` 中忽略。

## 数据库初始化

开发联调可运行：

```powershell
python scripts\init_dev_db.py
```

该脚本会在当前 `.env` 指向的 MySQL 中创建 `HotelSys`、核心表、视图、过程、触发器和演示数据。演示账号：

```text
front01 / 123456
admin01 / 123456
auditor01 / 123456
```

注意：该脚本用于本地联调。正式数据库结构以数据库组提交的 SQL 脚本为准。

## 分层结构

```text
app/
  main.py
  core/          配置、数据库连接、安全、统一响应、权限
  schemas/       Pydantic 入参模型
  repositories/  SQL 查询、视图和存储过程调用
  services/      业务规则和事务
  routers/       FastAPI 路由
tests/           契约测试
scripts/         本地配置和开发库初始化脚本
```

## 验证

```powershell
python -m pytest
```

健康检查返回 `database.status = ok` 表示后端已经能连接 MySQL。

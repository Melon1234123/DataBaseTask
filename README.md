# DataBaseTask

酒店管理系统课程项目，当前仓库包含需求/设计文档、最小前端和 Python 后端。

## 项目结构

```text
docs/                    需求分析、概念/逻辑设计、物理设计和接口规范
hotel-frontend-minimal/  前端最小实现，支持 Mock API 和真实 /api/v1 后端
backend/                 FastAPI 后端，连接 MySQL HotelSys
```

## 快速启动

后端推荐使用课程环境：

```powershell
conda activate bci
cd E:\DataBaseTask\backend
python -m pip install -r requirements.txt
python scripts\configure_env.py
python scripts\init_dev_db.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问地址：

- 前端页面：http://127.0.0.1:8000/
- 健康检查：http://127.0.0.1:8000/health
- API 文档：http://127.0.0.1:8000/docs

演示账号：

```text
front01 / 123456
admin01 / 123456
auditor01 / 123456
```

## 数据库密码和本地配置

不要把数据库密码写进 README、代码或提交记录。

每个协作者在本机运行：

```powershell
cd E:\DataBaseTask\backend
python scripts\configure_env.py
```

脚本会提示输入自己的 MySQL host、端口、用户名和密码，然后生成本地 `backend/.env`。`.env` 已被 `.gitignore` 忽略，不会提交到 GitHub。

如果密码里有 `@`、`#`、`:` 等特殊字符，也不要手动改 URL；让脚本自动编码即可。

## 后端说明

后端使用 FastAPI + SQLAlchemy + PyMySQL，统一返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "requestId": "req-..."
}
```

强一致业务优先调用数据库存储过程：

- `sp_create_reservation`
- `sp_check_in`
- `sp_checkout`
- `sp_start_cleaning`
- `sp_finish_cleaning`

开发联调用的 `python scripts\init_dev_db.py` 会创建本地测试表、视图、过程、触发器和演示数据，方便前后端先跑通。正式交付时以数据库组提供的 SQL 脚本为准。

## 协作注意

- 提交前运行 `git status --short --ignored`，确认 `backend/.env` 是 ignored 状态。
- 后端测试：`cd backend; python -m pytest`
- 前端真实接口联调请从 `http://127.0.0.1:8000/` 打开页面，保证前端和后端同源。

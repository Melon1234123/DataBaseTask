# DataBaseTask

酒店管理系统课程项目，当前仓库包含需求/设计文档、数据库 SQL、最小前端和 Python 后端。

## 项目结构

```text
docs/                    需求分析、概念/逻辑设计、物理设计和接口规范
HotelSys/                数据库组提供的建表、种子数据、索引、视图、过程和触发器 SQL
frontend/                真实 /api/v1 接口前端
hotel-frontend-minimal/  前端最小提交副本
backend/                 FastAPI 后端，连接 MySQL HotelSys
```

## 你现在该怎么操作

下面流程以 Windows + PowerShell 为例。路径如果不是 `E:\DataBaseTask`，改成你自己的仓库路径即可。

### 1. 拉取最新代码

```powershell
cd E:\DataBaseTask
git pull --ff-only
```

### 2. 准备 Python 后端环境

```powershell
conda activate bci
cd E:\DataBaseTask\backend
python -m pip install -r requirements.txt
```

### 3. 配置自己的数据库连接

不要把真实数据库密码写进 README、代码、`.env.example` 或提交记录。每个协作者只在自己电脑上生成本地 `backend/.env`：

```powershell
cd E:\DataBaseTask\backend
python scripts\configure_env.py
```

脚本会提示输入 MySQL host、端口、数据库名、用户名和密码，然后写入 `backend/.env`。这个文件已被 `.gitignore` 忽略，不会提交到 GitHub。

如果密码里有 `@`、`#`、`:` 等特殊字符，不要手动拼接连接串，让脚本自动编码即可。

### 4. 初始化数据库

推荐使用数据库组提供的官方 SQL。先确认本机 MySQL 服务已启动，再按顺序导入：

```powershell
cd E:\DataBaseTask
$mysql = "E:\mysql\bin\mysql.exe"  # 如果你的 mysql.exe 不在这里，改成自己的路径；已加入 PATH 时可写 "mysql"

& $mysql -u root -p --force -e "SOURCE E:/DataBaseTask/HotelSys/Schema.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/seed.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/Index.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/Views.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/Procedures.sql"
& $mysql -u root -p --force HotelSys -e "SOURCE E:/DataBaseTask/HotelSys/triggers.sql"
```

说明：

- `Schema.sql` 会创建/重建 `HotelSys` 数据库。
- `seed.sql` 当前主要是折扣、权限、操作类型等基础数据，不一定包含可登录账号。
- 如果前端登录失败，先确认 `UserAccount` 表里是否存在 `ApprovalStatus = '已启用'` 的账号。

如果只是想快速跑通后端和前端联调，也可以使用后端开发脚本初始化一套本地演示数据：

```powershell
cd E:\DataBaseTask\backend
python scripts\init_dev_db.py
```

开发脚本会创建测试数据和演示账号，方便先把接口流程跑通；正式联调以 `HotelSys/` 里的数据库 SQL 为准。

### 5. 启动后端

```powershell
cd E:\DataBaseTask\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后访问：

- 前端页面：http://127.0.0.1:8000/
- 健康检查：http://127.0.0.1:8000/health
- API 文档：http://127.0.0.1:8000/docs

如果 `/health` 里 `database.status` 是 `ok`，说明后端已经连上 MySQL。  
如果是 `unavailable`，优先检查 `backend/.env` 里的数据库名、用户名、密码、端口是否正确。

### 6. 前后端联调

1. 打开 http://127.0.0.1:8000/。
2. 用数据库里已启用的账号登录。
3. 按业务流程测试客户、房型、房间、预定、入住、结账、清扫、审计等功能。

本地开发脚本默认演示账号：

```text
front01 / 123456
admin01 / 123456
auditor01 / 123456
```

## 后端接口说明

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

主要接口都挂在 `/api/v1` 下，完整参数可以看 http://127.0.0.1:8000/docs。

## 提交前检查

```powershell
cd E:\DataBaseTask
git status --short --ignored
```

确认：

- `backend/.env` 没有被加入暂存区，最多只应该显示为 `!! backend/.env`。
- 不要提交真实密码、个人数据库配置、日志和缓存文件。
- 后端测试通过：

```powershell
cd E:\DataBaseTask\backend
python -m pytest
```

提交示例：

```powershell
cd E:\DataBaseTask
git add README.md
git commit -m "docs: update setup workflow"
git push origin main
```

如果不小心把 `.env` 暂存了，先取消暂存：

```powershell
git restore --staged backend/.env
```

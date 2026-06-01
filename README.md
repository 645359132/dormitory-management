# 学生宿舍管理系统

前端使用 Vite + Vue 3，后端使用 uv + FastAPI，数据库使用 Microsoft SQL Server。后端不使用 ORM，所有业务接口均通过 `pyodbc` 执行参数化 SQL。

## 目录

- `docs/init.sql`：SQL Server 初始化脚本，包含表、索引、视图、触发器、存储过程和演示数据。
- `docs/extracted/`：从需求 Word 文档抽取出的纯文本，便于后续检索。
- `backend/`：FastAPI 接口服务。
- `frontend/`：Vue 单页管理工作台。

## 数据库

在 SQL Server 中执行。若本机是 SQL Server Express，推荐使用：

```powershell
sqlcmd -S localhost\SQLEXPRESS -E -C -f 65001 -i docs\init.sql
```

其中 `-C` 用于信任本地开发证书，`-f 65001` 用于按 UTF-8 读取中文脚本。

也可以在 SSMS 中打开 `docs/init.sql` 后直接执行。若使用 SSMS，请确认文件按 UTF-8 正常显示中文。

```sql
:r docs/init.sql
```

初始化账号：

- 管理员：`admin01` / `admin123`
- 学生：`24050710` / `24050710`

## 后端

复制 `backend/.env.example` 为 `backend/.env`，按本机 SQL Server 修改连接参数。

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：`http://127.0.0.1:8000/api/health`

## 前端

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

页面地址：`http://127.0.0.1:5173/`

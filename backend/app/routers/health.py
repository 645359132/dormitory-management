"""
学生宿舍管理系统 - 健康检查接口
=============================
提供数据库连通性检测端点。
"""
from typing import Any

from fastapi import APIRouter

from ..db import DatabaseUnavailable, fetch_one


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    """健康检查：尝试执行简单查询以确认数据库是否可用。

    返回 status="ok" 表示一切正常，status="degraded" 表示数据库不可达但服务仍在运行。
    """
    try:
        fetch_one("SELECT 1 AS ok")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        if isinstance(exc, DatabaseUnavailable):
            return {"status": "degraded", "database": str(exc)}
        raise

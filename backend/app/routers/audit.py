"""
学生宿舍管理系统 - 审计日志接口
===============================
提供关键操作日志查询端点。
"""
from typing import Any

from fastapi import APIRouter, Depends

from ..api_utils import raise_db
from ..db import fetch_all
from ..security import CurrentUser, require_admin


router = APIRouter(tags=["audit"])


@router.get("/audit-logs")
def list_audit_logs(_: CurrentUser = Depends(require_admin)) -> list[dict[str, Any]]:
    """查询最近 100 条审计日志。"""
    try:
        return fetch_all(
            """
            SELECT TOP 100 LogId AS log_id,
                           OperatorId AS operator_id,
                           ActionType AS action_type,
                           TargetId AS target_id,
                           Detail AS detail,
                           CreatedAt AS created_at
            FROM AuditLog
            ORDER BY LogId DESC
            """
        )
    except Exception as exc:
        raise_db(exc)

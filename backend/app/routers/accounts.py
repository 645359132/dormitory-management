"""
学生宿舍管理系统 - 账号与权限管理接口
=====================================
提供登录账号的增删改查和角色配置。
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..api_utils import raise_db
from ..db import connection, fetch_all
from ..schemas import AccountCreate, AccountUpdate
from ..security import CurrentUser, hash_password, require_admin


router = APIRouter(prefix="/accounts", tags=["accounts"])


def _ensure_student_exists(cursor: Any, account: str, role: str | None) -> None:
    """学生角色账号必须关联到已存在的学生。"""
    if role != "student":
        return
    cursor.execute("SELECT 1 FROM Student WHERE StudentId = ?", (account,))
    if cursor.fetchone() is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="学生角色账号必须关联到已有学生")


@router.get("")
def list_accounts(_: CurrentUser = Depends(require_admin)) -> list[dict[str, Any]]:
    """查询全部系统登录账号及角色。"""
    try:
        return fetch_all(
            """
            SELECT AdminId AS account, Role AS role
            FROM Admin
            ORDER BY CASE WHEN Role = 'admin' THEN 0 ELSE 1 END, AdminId
            """
        )
    except Exception as exc:
        raise_db(exc)


@router.post("")
def create_account(
    payload: AccountCreate,
    current: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """创建登录账号并配置角色。"""
    try:
        with connection() as conn:
            cursor = conn.cursor()
            _ensure_student_exists(cursor, payload.account, payload.role)
            cursor.execute(
                "INSERT INTO Admin(AdminId, Password, Role) VALUES (?, ?, ?)",
                (payload.account, hash_password(payload.password), payload.role),
            )
            cursor.execute(
                """
                INSERT INTO AuditLog(OperatorId, ActionType, TargetId, Detail)
                VALUES (?, N'账号创建', ?, ?)
                """,
                (current.account, payload.account, f"角色: {payload.role}"),
            )
        return {"message": "账号已创建"}
    except Exception as exc:
        raise_db(exc)


@router.patch("/{account}")
def update_account(
    account: str,
    payload: AccountUpdate,
    current: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """修改账号密码或角色。"""
    try:
        data = payload.model_dump(exclude_unset=True)
        if account == current.account and data.get("role") == "student":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="不能降低当前登录账号的权限")

        with connection() as conn:
            cursor = conn.cursor()
            _ensure_student_exists(cursor, account, data.get("role"))
            sets: list[str] = []
            params: list[Any] = []
            if payload.password:
                sets.append("Password = ?")
                params.append(hash_password(payload.password))
            if "role" in data:
                sets.append("Role = ?")
                params.append(payload.role)
            if not sets:
                return {"message": "没有变更"}

            params.append(account)
            cursor.execute(f"UPDATE Admin SET {', '.join(sets)} WHERE AdminId = ?", tuple(params))
            if cursor.rowcount == 0:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="账号不存在")
            cursor.execute(
                """
                INSERT INTO AuditLog(OperatorId, ActionType, TargetId, Detail)
                VALUES (?, N'账号修改', ?, N'修改账号密码或角色')
                """,
                (current.account, account),
            )
        return {"message": "账号已更新"}
    except Exception as exc:
        raise_db(exc)


@router.delete("/{account}")
def delete_account(
    account: str,
    current: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """删除登录账号；当前登录账号不可删除。"""
    try:
        if account == current.account:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录账号")
        with connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Admin WHERE AdminId = ?", (account,))
            if cursor.rowcount == 0:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="账号不存在")
            cursor.execute(
                """
                INSERT INTO AuditLog(OperatorId, ActionType, TargetId, Detail)
                VALUES (?, N'账号删除', ?, N'删除登录账号')
                """,
                (current.account, account),
            )
        return {"message": "账号已删除"}
    except Exception as exc:
        raise_db(exc)

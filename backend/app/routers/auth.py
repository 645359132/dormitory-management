"""
学生宿舍管理系统 - 认证接口
===========================
提供登录认证和当前用户查询端点。
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..api_utils import raise_db
from ..db import fetch_one
from ..schemas import LoginRequest
from ..security import CurrentUser, create_access_token, require_user, verify_password


router = APIRouter(tags=["auth"])


@router.post("/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    """用户登录：验证账号密码，返回 JWT 令牌和用户信息。

    管理员直接返回 token + account + role；
    学生额外返回 Student 表中的基础信息（学号、姓名、宿舍）。
    """
    try:
        # 查询 Admin 表验证账号密码
        account = fetch_one(
            """
            SELECT AdminId AS account, Password AS password, Role AS role
            FROM Admin
            WHERE AdminId = ?
            """,
            (payload.account,),
        )
        if account is None or not verify_password(payload.password, account["password"]):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")

        # 生成访问令牌
        token = create_access_token(account["account"], account["role"])
        response: dict[str, Any] = {
            "token": token,
            "account": account["account"],
            "role": account["role"],
        }
        # 学生用户附带本人档案信息
        if account["role"] == "student":
            response["student"] = fetch_one(
                """
                SELECT StudentId AS student_id, Name AS name, BuildingNo AS building_no, RoomNo AS room_no
                FROM Student
                WHERE StudentId = ?
                """,
                (account["account"],),
            )
        return response
    except Exception as exc:
        raise_db(exc)


@router.get("/me")
def me(current: CurrentUser = Depends(require_user)) -> CurrentUser:
    """获取当前登录用户信息（需携带有效令牌）。"""
    return current

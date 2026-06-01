"""
学生宿舍管理系统 - 安全认证模块
=============================
提供密码哈希/验证、自签名 JWT 令牌的生成与解析，以及基于角色的权限守卫。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings


# 用户角色类型：管理员或学生
Role = Literal["admin", "student"]
# Bearer 令牌认证方案（auto_error=False 表示令牌缺失时不自动报错）
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """当前登录用户信息（不可变）。"""
    account: str  # 账号
    role: Role    # 角色


def _b64(data: bytes) -> str:
    """URL 安全的 Base64 编码（去掉末尾 = 填充符）。"""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    """URL 安全的 Base64 解码（自动补齐缺失的 = 填充符）。"""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str) -> str:
    """使用 SHA-256 算法对明文密码进行哈希。"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_password: str) -> bool:
    """验证明文密码是否与数据库中存储的密码匹配。

    支持三种存储格式：
    1. 64 位纯 SHA-256 哈希值
    2. "sha256$" 前缀格式
    3. 明文密码（向后兼容）
    """
    stored = stored_password.strip()
    digest = hash_password(password)
    if len(stored) == 64 and all(char in "0123456789abcdefABCDEF" for char in stored):
        return hmac.compare_digest(digest.lower(), stored.lower())
    if stored.startswith("sha256$"):
        return hmac.compare_digest(f"sha256${digest}", stored)
    return hmac.compare_digest(password, stored)


def create_access_token(account: str, role: Role) -> str:
    """生成自签名访问令牌（JWT 风格），包含账号、角色和过期时间。

    令牌格式：base64(payload).base64(HMAC-SHA256 签名)
    """
    settings = get_settings()
    payload = {
        "sub": account,
        "role": role,
        "exp": int(time.time()) + settings.token_expire_minutes * 60,
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(settings.token_secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256)
    return f"{body}.{_b64(signature.digest())}"


def parse_access_token(token: str) -> CurrentUser:
    """解析并验证访问令牌，提取其中的用户信息。

    验证：
    1. 签名是否正确
    2. 令牌是否过期
    3. 角色是否合法
    """
    try:
        body, signature = token.split(".", 1)
        expected = hmac.new(
            get_settings().token_secret.encode("utf-8"),
            body.encode("ascii"),
            hashlib.sha256,
        )
        if not hmac.compare_digest(_b64(expected.digest()), signature):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(body))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("expired")
        role = payload["role"]
        if role not in {"admin", "student"}:
            raise ValueError("bad role")
        return CurrentUser(account=payload["sub"], role=role)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效") from exc


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> CurrentUser:
    """FastAPI 依赖注入：要求用户已登录（任意角色），返回当前用户信息。"""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return parse_access_token(credentials.credentials)


def require_admin(current: CurrentUser = Depends(require_user)) -> CurrentUser:
    """FastAPI 依赖注入：要求用户具有管理员角色。"""
    if current.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current


def require_student(current: CurrentUser = Depends(require_user)) -> CurrentUser:
    """FastAPI 依赖注入：要求用户具有学生角色。"""
    if current.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="需要学生账号")
    return current

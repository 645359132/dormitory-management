"""
学生宿舍管理系统 - 配置模块
=========================
负责加载 .env 环境变量文件，提供全局设置和数据库连接字符串构建。
"""
from functools import lru_cache
from os import environ, getenv
from pathlib import Path


def _load_env_file() -> None:
    """从项目根目录的 .env 文件加载环境变量（不会覆盖已有的环境变量）。"""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# 模块加载时自动执行环境变量加载
_load_env_file()


class Settings:
    """全局配置项，包含 JWT、CORS 和数据库相关参数。"""
    app_name = "Dormitory Management API"
    # JWT 令牌密钥和过期时间（分钟）
    token_secret = getenv("APP_SECRET_KEY", "dev-dormitory-secret")
    token_expire_minutes = int(getenv("TOKEN_EXPIRE_MINUTES", "720"))
    # CORS 允许的前端域名列表
    cors_origins = [
        origin.strip()
        for origin in getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]

    # SQL Server 数据库连接参数
    db_driver = getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    db_server = getenv("DB_SERVER", "localhost")
    db_name = getenv("DB_NAME", "DormMgmt")
    db_user = getenv("DB_USER")
    db_password = getenv("DB_PASSWORD")
    db_trusted = getenv("DB_TRUSTED_CONNECTION", "yes").lower() in {
        "1",
        "true",
        "yes",
        "y",
    }
    db_trust_cert = getenv("DB_TRUST_SERVER_CERTIFICATE", "yes").lower() in {
        "1",
        "true",
        "yes",
        "y",
    }
    db_timeout = int(getenv("DB_TIMEOUT", "5"))


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例（带缓存）。"""
    return Settings()


def build_connection_string() -> str:
    """根据当前配置构建 SQL Server 数据库连接字符串。"""
    settings = get_settings()
    parts = [
        f"DRIVER={{{settings.db_driver}}}",
        f"SERVER={settings.db_server}",
        f"DATABASE={settings.db_name}",
        "Encrypt=yes",
        f"TrustServerCertificate={'yes' if settings.db_trust_cert else 'no'}",
    ]
    # 根据是否使用 Windows 集成认证选择不同的认证方式
    if settings.db_trusted:
        parts.append("Trusted_Connection=yes")
    else:
        if not settings.db_user or settings.db_password is None:
            raise RuntimeError("DB_USER and DB_PASSWORD are required when trusted login is disabled")
        parts.append(f"UID={settings.db_user}")
        parts.append(f"PWD={settings.db_password}")
    return ";".join(parts)

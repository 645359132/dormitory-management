"""
学生宿舍管理系统 - 数据库操作模块
=============================
封装 pyodbc 连接管理和 SQL 查询辅助函数，提供统一的数据库访问接口。
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any, Iterable, Iterator, Sequence

from .config import build_connection_string, get_settings


class DatabaseUnavailable(RuntimeError):
    """数据库不可用异常，在连接失败或 pyodbc 未安装时抛出。"""
    pass


def _pyodbc():
    """延迟导入 pyodbc 模块，避免在未安装时导致整个应用崩溃。"""
    try:
        return import_module("pyodbc")
    except ImportError as exc:
        raise DatabaseUnavailable("pyodbc is not installed. Run `uv sync` in backend first.") from exc


@contextmanager
def connection() -> Iterator[Any]:
    """数据库连接上下文管理器，自动处理事务提交/回滚和连接关闭。

    用法：with connection() as conn: ...
    """
    settings = get_settings()
    pyodbc = _pyodbc()
    try:
        conn = pyodbc.connect(build_connection_string(), timeout=settings.db_timeout)
    except Exception as exc:  # pyodbc raises driver-specific subclasses.
        raise DatabaseUnavailable(f"Cannot connect to SQL Server: {exc}") from exc

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _convert(value: Any) -> Any:
    """将数据库返回值转换为 Python 友好格式（去空白、Decimal 转 float、日期转 ISO 字符串）。"""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def rows_to_dicts(cursor: Any) -> list[dict[str, Any]]:
    """将游标中的所有行转换为字典列表，键名为列名。"""
    columns = [column[0] for column in cursor.description or []]
    return [
        {column: _convert(value) for column, value in zip(columns, row)}
        for row in cursor.fetchall()
    ]


def fetch_all(sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    """执行 SELECT 查询并返回所有结果行（字典列表）。"""
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params or ()))
        return rows_to_dicts(cursor)


def fetch_one(sql: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
    """执行 SELECT 查询并返回第一行结果（字典），无结果时返回 None。"""
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: Sequence[Any] | None = None) -> int:
    """执行非查询 SQL 语句（INSERT/UPDATE/DELETE），返回受影响行数。"""
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params or ()))
        return cursor.rowcount


def execute_many(sql: str, rows: Iterable[Sequence[Any]]) -> None:
    """批量执行 SQL 语句（开启 fast_executemany 以提高性能）。"""
    with connection() as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True
        cursor.executemany(sql, list(rows))

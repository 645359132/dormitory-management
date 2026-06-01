"""
学生宿舍管理系统 - API 工具函数模块
===============================
提供路由中复用的辅助函数，包括异常转换、ID 生成、床位同步、容量校验和学生信息聚合。
"""
from __future__ import annotations

from datetime import date
from secrets import randbelow
from typing import Any

from fastapi import HTTPException, status

from .db import DatabaseUnavailable, rows_to_dicts


def raise_db(exc: Exception) -> None:
    """将数据库异常转换为 HTTP 异常。

    - HTTPException 直接重新抛出
    - DatabaseUnavailable 转为 503
    - 其他异常取第一行错误信息转为 400
    """
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, DatabaseUnavailable):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    message = str(exc).splitlines()[0]
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=message) from exc


def new_id(prefix: str) -> str:
    """生成带日期前缀的唯一 ID。

    格式：{prefix}{YYYYMMDD}{7位随机数}，最长 16 字符
    示例：new_id("B") -> "B202506011234567"
    """
    return f"{prefix}{date.today():%Y%m%d}{randbelow(10_000_000):07d}"[:16]


def sync_bed_used(cursor: Any) -> None:
    """同步宿舍表 BedUsed 字段：根据 Student 表统计每间宿舍实际入住人数并更新。"""
    cursor.execute(
        """
        UPDATE d
        SET BedUsed = ISNULL(s.used_count, 0)
        FROM Dormitory AS d
        LEFT JOIN (
            SELECT BuildingNo, RoomNo, COUNT(*) AS used_count
            FROM Student
            WHERE BuildingNo IS NOT NULL AND RoomNo IS NOT NULL
            GROUP BY BuildingNo, RoomNo
        ) AS s
            ON s.BuildingNo = d.BuildingNo AND s.RoomNo = d.RoomNo
        """
    )


def ensure_room_capacity(
    cursor: Any,
    building_no: str | None,
    room_no: str | None,
    exclude_student_id: str | None = None,
) -> None:
    """校验宿舍是否有空余床位。

    若楼栋和房间均为 None 则跳过校验；若只填了一个则为无效；
    否则查询该宿舍剩余床位，超过容量则抛出异常。
    exclude_student_id 用于在学生住宿调整时排除该学生自身。
    """
    if building_no is None and room_no is None:
        return
    if not building_no or not room_no:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="楼栋和房间必须同时填写")

    # 查询宿舍容量
    cursor.execute(
        """
        SELECT BedTotal
        FROM Dormitory
        WHERE BuildingNo = ? AND RoomNo = ?
        """,
        (building_no, room_no),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="宿舍不存在")

    # 查询当前入住人数（排除指定学生）
    params: list[Any] = [building_no, room_no]
    condition = ""
    if exclude_student_id:
        condition = " AND StudentId <> ?"
        params.append(exclude_student_id)

    cursor.execute(
        f"""
        SELECT COUNT(*) AS used_count
        FROM Student
        WHERE BuildingNo = ? AND RoomNo = ?{condition}
        """,
        tuple(params),
    )
    used_count = cursor.fetchone()[0]
    if used_count >= row[0]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="该宿舍已住满")


def student_summary(cursor: Any, student_id: str) -> dict[str, Any]:
    """获取学生基础信息及所属宿舍详情。

    返回值包含：学号、姓名、性别、专业、班级、电话、楼栋、房间号、床位总数、已用床位数、宿舍长学号。
    若学生不存在则抛出 404。
    """
    cursor.execute(
        """
        SELECT s.StudentId AS student_id,
               s.Name AS name,
               s.Gender AS gender,
               s.Major AS major,
               s.[Class] AS class_name,
               s.Phone AS phone,
               s.BuildingNo AS building_no,
               s.RoomNo AS room_no,
               d.BedTotal AS bed_total,
               d.BedUsed AS bed_used,
               d.HeadStudentId AS head_student_id
        FROM Student AS s
        LEFT JOIN Dormitory AS d
            ON d.BuildingNo = s.BuildingNo AND d.RoomNo = s.RoomNo
        WHERE s.StudentId = ?
        """,
        (student_id,),
    )
    rows = rows_to_dicts(cursor)
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="学生不存在")
    return rows[0]

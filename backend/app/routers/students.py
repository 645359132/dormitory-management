"""
学生宿舍管理系统 - 学生管理接口
===============================
提供学生的增删改查、住宿分配和密码重置操作。
"""
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from ..api_utils import ensure_room_capacity, raise_db, student_summary, sync_bed_used
from ..db import connection, fetch_all
from ..schemas import PasswordReset, StudentBatchImport, StudentCreate, StudentUpdate
from ..security import CurrentUser, hash_password, require_admin


router = APIRouter(prefix="/students", tags=["students"])


def _move_in_date(building_no: str | None, room_no: str | None, value: date | None) -> date | None:
    """已分配宿舍时默认今天入住，退宿时清空入住日期。"""
    return value or date.today() if building_no and room_no else None


def _student_password(payload: StudentCreate) -> str:
    """未指定初始密码时使用学号。"""
    return payload.password or payload.student_id


@router.get("")
def list_students(
    q: str | None = Query(default=None),
    building_no: str | None = None,
    room_no: str | None = None,
    residence_status: str | None = Query(default=None, pattern="^(assigned|unassigned)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """查询学生列表，支持按关键字搜索和按宿舍筛选。

    参数：
    - q: 搜索关键字（匹配学号、姓名、专业、班级）
    - building_no: 按楼栋筛选
    - room_no: 按房间筛选
    """
    try:
        conditions = ["1 = 1"]
        params: list[Any] = []
        if q:
            conditions.append(
                "(s.StudentId LIKE ? OR s.Name LIKE ? OR s.Major LIKE ? OR s.[Class] LIKE ? "
                "OR s.Phone LIKE ? OR s.BuildingNo LIKE ? OR s.RoomNo LIKE ?)"
            )
            like = f"%{q}%"
            params.extend([like, like, like, like, like, like, like])
        if building_no:
            conditions.append("s.BuildingNo = ?")
            params.append(building_no)
        if room_no:
            conditions.append("s.RoomNo = ?")
            params.append(room_no)
        if residence_status == "assigned":
            conditions.append("s.BuildingNo IS NOT NULL AND s.RoomNo IS NOT NULL")
        elif residence_status == "unassigned":
            conditions.append("(s.BuildingNo IS NULL OR s.RoomNo IS NULL)")

        where = " AND ".join(conditions)
        total_row = fetch_all(
            f"SELECT COUNT(*) AS total FROM Student AS s WHERE {where}",
            tuple(params),
        )
        total = total_row[0]["total"] if total_row else 0
        offset = (page - 1) * page_size

        items = fetch_all(
            f"""
            SELECT s.StudentId AS student_id,
                   s.Name AS name,
                   s.Gender AS gender,
                   s.Major AS major,
                   s.[Class] AS class_name,
                   s.Phone AS phone,
                   s.BuildingNo AS building_no,
                   s.RoomNo AS room_no,
                   s.MoveInDate AS move_in_date,
                   d.HeadStudentId AS head_student_id
            FROM Student AS s
            LEFT JOIN Dormitory AS d
                ON d.BuildingNo = s.BuildingNo AND d.RoomNo = s.RoomNo
            WHERE {where}
            ORDER BY s.BuildingNo, s.RoomNo, s.StudentId
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            tuple([*params, offset, page_size]),
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except Exception as exc:
        raise_db(exc)


@router.post("")
def create_student(
    payload: StudentCreate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """创建新学生，同时在 Admin 表创建登录账号。

    流程：
    1. 同步床位使用情况
    2. 校验目标宿舍是否有空余床位
    3. 插入 Student 表
    4. 若 Admin 表中不存在同账号，则创建学生登录账号
    5. 再次同步床位使用情况
    """
    try:
        with connection() as conn:
            cursor = conn.cursor()
            # 同步床位并校验容量
            sync_bed_used(cursor)
            ensure_room_capacity(cursor, payload.building_no, payload.room_no)
            # 插入学生记录
            cursor.execute(
                """
                INSERT INTO Student(StudentId, Name, Gender, Major, [Class], Phone, BuildingNo, RoomNo, MoveInDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.student_id,
                    payload.name,
                    payload.gender,
                    payload.major,
                    payload.class_name,
                    payload.phone,
                    payload.building_no,
                    payload.room_no,
                    _move_in_date(payload.building_no, payload.room_no, payload.move_in_date),
                ),
            )
            # 创建登录账号（若不存在）
            cursor.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM Admin WHERE AdminId = ?)
                INSERT INTO Admin(AdminId, Password, Role) VALUES (?, ?, 'student')
                """,
                (payload.student_id, payload.student_id, hash_password(_student_password(payload))),
            )
            sync_bed_used(cursor)
        return {"message": "学生已创建"}
    except Exception as exc:
        raise_db(exc)


@router.post("/import")
def import_students(
    payload: StudentBatchImport,
    current: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """批量导入学生，并为每名学生自动生成登录账号。"""
    try:
        with connection() as conn:
            cursor = conn.cursor()
            sync_bed_used(cursor)
            for student in payload.students:
                ensure_room_capacity(cursor, student.building_no, student.room_no)
                cursor.execute(
                    """
                    INSERT INTO Student(StudentId, Name, Gender, Major, [Class], Phone, BuildingNo, RoomNo, MoveInDate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        student.student_id,
                        student.name,
                        student.gender,
                        student.major,
                        student.class_name,
                        student.phone,
                        student.building_no,
                        student.room_no,
                        _move_in_date(student.building_no, student.room_no, student.move_in_date),
                    ),
                )
                cursor.execute(
                    """
                    IF NOT EXISTS (SELECT 1 FROM Admin WHERE AdminId = ?)
                    INSERT INTO Admin(AdminId, Password, Role) VALUES (?, ?, 'student')
                    """,
                    (student.student_id, student.student_id, hash_password(_student_password(student))),
                )
            sync_bed_used(cursor)
            cursor.execute(
                """
                INSERT INTO AuditLog(OperatorId, ActionType, TargetId, Detail)
                VALUES (?, N'学生导入', NULL, ?)
                """,
                (current.account, f"批量导入 {len(payload.students)} 名学生"),
            )
        return {"message": f"已导入 {len(payload.students)} 名学生", "created_count": len(payload.students)}
    except Exception as exc:
        raise_db(exc)


@router.patch("/{student_id}")
def update_student(
    student_id: str,
    payload: StudentUpdate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """更新学生信息，支持修改宿舍分配（自动校验床位容量）。"""
    try:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            return {"message": "没有变更"}

        with connection() as conn:
            cursor = conn.cursor()
            # 获取学生当前状态
            current = student_summary(cursor, student_id)
            target_building = data.get("building_no", current["building_no"])
            target_room = data.get("room_no", current["room_no"])
            sync_bed_used(cursor)
            ensure_room_capacity(cursor, target_building, target_room, exclude_student_id=student_id)
            room_changed = target_building != current["building_no"] or target_room != current["room_no"]
            if room_changed or "move_in_date" in data:
                data["move_in_date"] = _move_in_date(target_building, target_room, data.get("move_in_date"))
            if room_changed:
                cursor.execute("UPDATE Dormitory SET HeadStudentId = NULL WHERE HeadStudentId = ?", (student_id,))

            # 字段名映射
            field_map = {
                "name": "Name",
                "gender": "Gender",
                "major": "Major",
                "class_name": "[Class]",
                "phone": "Phone",
                "building_no": "BuildingNo",
                "room_no": "RoomNo",
                "move_in_date": "MoveInDate",
            }
            sets: list[str] = []
            params: list[Any] = []
            for key, column in field_map.items():
                if key in data:
                    sets.append(f"{column} = ?")
                    params.append(data[key])

            params.append(student_id)
            cursor.execute(f"UPDATE Student SET {', '.join(sets)} WHERE StudentId = ?", tuple(params))
            sync_bed_used(cursor)
        return {"message": "学生已更新"}
    except Exception as exc:
        raise_db(exc)


@router.delete("/{student_id}")
def delete_student(
    student_id: str,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """删除学生，同时删除其 Admin 登录账号，并同步床位。"""
    try:
        with connection() as conn:
            cursor = conn.cursor()
            # 先解除宿舍长引用，再删登录账号和学生记录
            cursor.execute("UPDATE Dormitory SET HeadStudentId = NULL WHERE HeadStudentId = ?", (student_id,))
            cursor.execute("DELETE FROM Admin WHERE AdminId = ? AND Role = 'student'", (student_id,))
            cursor.execute("DELETE FROM Student WHERE StudentId = ?", (student_id,))
            sync_bed_used(cursor)
        return {"message": "学生已删除"}
    except Exception as exc:
        raise_db(exc)


@router.post("/{student_id}/reset-password")
def reset_student_password(
    student_id: str,
    payload: PasswordReset,
    current: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """管理员重置学生登录密码，并记录审计日志。"""
    try:
        with connection() as conn:
            cursor = conn.cursor()
            # 更新密码
            cursor.execute(
                """
                UPDATE Admin
                SET Password = ?
                WHERE AdminId = ? AND Role = 'student'
                """,
                (hash_password(payload.password), student_id),
            )
            # 记录审计日志
            cursor.execute(
                """
                INSERT INTO AuditLog(OperatorId, ActionType, TargetId, Detail)
                VALUES (?, N'密码重置', ?, N'管理员重置学生账号密码')
                """,
                (current.account, student_id),
            )
        return {"message": "密码已重置"}
    except Exception as exc:
        raise_db(exc)

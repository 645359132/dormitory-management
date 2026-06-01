"""
学生宿舍管理系统 - 宿舍管理接口
===============================
提供宿舍的增删改查操作。
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..api_utils import raise_db
from ..db import connection, fetch_all
from ..schemas import DormitoryCreate, DormitoryUpdate
from ..security import CurrentUser, require_admin, require_user


router = APIRouter(prefix="/dormitories", tags=["dormitories"])


@router.get("")
def list_dormitories(
    vacant_only: bool = False,
    _: CurrentUser = Depends(require_user),
) -> list[dict[str, Any]]:
    """查询宿舍列表。

    可选参数：
    - vacant_only: 仅返回有空余床位的宿舍
    """
    try:
        where = "WHERE d.BedUsed < d.BedTotal" if vacant_only else ""
        return fetch_all(
            f"""
            SELECT d.BuildingNo AS building_no,
                   d.RoomNo AS room_no,
                   d.BedTotal AS bed_total,
                   d.BedUsed AS bed_used,
                   d.BedTotal - d.BedUsed AS vacant_beds,
                   d.HeadStudentId AS head_student_id,
                   h.Name AS head_name
            FROM Dormitory AS d
            LEFT JOIN Student AS h ON h.StudentId = d.HeadStudentId
            {where}
            ORDER BY d.BuildingNo, d.RoomNo
            """
        )
    except Exception as exc:
        raise_db(exc)


@router.post("")
def create_dormitory(
    payload: DormitoryCreate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """创建新宿舍房间。"""
    try:
        with connection() as conn:
            conn.cursor().execute(
                """
                INSERT INTO Dormitory(BuildingNo, RoomNo, BedTotal, HeadStudentId)
                VALUES (?, ?, ?, ?)
                """,
                (payload.building_no, payload.room_no, payload.bed_total, payload.head_student_id),
            )
        return {"message": "宿舍已创建"}
    except Exception as exc:
        raise_db(exc)


@router.patch("/{building_no}/{room_no}")
def update_dormitory(
    building_no: str,
    room_no: str,
    payload: DormitoryUpdate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """更新宿舍信息（床位总数和/或宿舍长）。

    校验：床位数不能小于当前实际入住人数。
    """
    try:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            return {"message": "没有变更"}

        with connection() as conn:
            cursor = conn.cursor()
            # 如果修改了床位数，需校验不低于当前入住人数
            if "bed_total" in data:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS used_count
                    FROM Student
                    WHERE BuildingNo = ? AND RoomNo = ?
                    """,
                    (building_no, room_no),
                )
                if cursor.fetchone()[0] > payload.bed_total:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="床位数不能小于当前入住人数")

            sets: list[str] = []
            params: list[Any] = []
            if "bed_total" in data:
                sets.append("BedTotal = ?")
                params.append(payload.bed_total)
            if "head_student_id" in data:
                sets.append("HeadStudentId = ?")
                params.append(payload.head_student_id)

            params.extend([building_no, room_no])
            cursor.execute(
                f"UPDATE Dormitory SET {', '.join(sets)} WHERE BuildingNo = ? AND RoomNo = ?",
                tuple(params),
            )
        return {"message": "宿舍已更新"}
    except Exception as exc:
        raise_db(exc)


@router.delete("/{building_no}/{room_no}")
def delete_dormitory(
    building_no: str,
    room_no: str,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """删除指定宿舍。"""
    try:
        with connection() as conn:
            conn.cursor().execute(
                "DELETE FROM Dormitory WHERE BuildingNo = ? AND RoomNo = ?",
                (building_no, room_no),
            )
        return {"message": "宿舍已删除"}
    except Exception as exc:
        raise_db(exc)

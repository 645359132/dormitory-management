"""
学生宿舍管理系统 - 出入登记接口
===============================
提供物品寄存登记和访客登记功能。
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..api_utils import new_id, raise_db, student_summary
from ..db import connection, fetch_all
from ..schemas import ItemRecordCreate, ItemRecordUpdate, VisitorRecordCreate
from ..security import CurrentUser, require_admin


router = APIRouter(prefix="/access", tags=["access"])


@router.get("/items")
def list_items(_: CurrentUser = Depends(require_admin)) -> list[dict[str, Any]]:
    """查询物品寄存记录列表（仅管理员）。"""
    try:
        return fetch_all(
            """
            SELECT i.ItemId AS item_id,
                   i.StudentId AS student_id,
                   s.Name AS student_name,
                   i.ItemName AS item_name,
                   i.Action AS action,
                   i.Quantity AS quantity,
                   i.Status AS status,
                   i.RegisterTime AS register_time,
                   i.Remark AS remark
            FROM ItemRecord AS i
            LEFT JOIN Student AS s ON s.StudentId = i.StudentId
            ORDER BY i.RegisterTime DESC
            """
        )
    except Exception as exc:
        raise_db(exc)


@router.post("/items")
def create_item(
    payload: ItemRecordCreate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """登记物品存取记录。"""
    try:
        item_id = new_id("I")
        with connection() as conn:
            conn.cursor().execute(
                """
                INSERT INTO ItemRecord(ItemId, StudentId, ItemName, Action, Quantity, Remark)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    payload.student_id,
                    payload.item_name,
                    payload.action,
                    payload.quantity,
                    payload.remark,
                ),
            )
        return {"message": "物品记录已登记", "item_id": item_id}
    except Exception as exc:
        raise_db(exc)


@router.patch("/items/{item_id}")
def update_item(
    item_id: str,
    payload: ItemRecordUpdate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """更新物品记录状态（如标记已归还）。"""
    try:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            return {"message": "没有变更"}

        sets: list[str] = []
        params: list[Any] = []
        if "status" in data:
            sets.append("Status = ?")
            params.append(payload.status)
        if "remark" in data:
            sets.append("Remark = ?")
            params.append(payload.remark)

        params.append(item_id)
        with connection() as conn:
            conn.cursor().execute(f"UPDATE ItemRecord SET {', '.join(sets)} WHERE ItemId = ?", tuple(params))
        return {"message": "物品记录已更新"}
    except Exception as exc:
        raise_db(exc)


@router.get("/visitors")
def list_visitors(_: CurrentUser = Depends(require_admin)) -> list[dict[str, Any]]:
    """查询访客记录列表（仅管理员）。"""
    try:
        return fetch_all(
            """
            SELECT v.VisitorId AS visitor_id,
                   v.VisitorName AS visitor_name,
                   v.Phone AS phone,
                   v.VisitStudentId AS visit_student_id,
                   s.Name AS student_name,
                   v.BuildingNo AS building_no,
                   v.RoomNo AS room_no,
                   v.EnterTime AS enter_time,
                   v.LeaveTime AS leave_time,
                   v.Status AS status,
                   v.Remark AS remark
            FROM VisitorRecord AS v
            LEFT JOIN Student AS s ON s.StudentId = v.VisitStudentId
            ORDER BY v.EnterTime DESC
            """
        )
    except Exception as exc:
        raise_db(exc)


@router.post("/visitors")
def create_visitor(
    payload: VisitorRecordCreate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """登记访客信息，自动查询被访学生所在宿舍。"""
    try:
        visitor_id = new_id("V")
        with connection() as conn:
            cursor = conn.cursor()
            # 获取被访学生信息，确认其已分配宿舍
            student = student_summary(cursor, payload.visit_student_id)
            if student["building_no"] is None or student["room_no"] is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="被访学生尚未分配宿舍")
            cursor.execute(
                """
                INSERT INTO VisitorRecord(VisitorId, VisitorName, Phone, VisitStudentId, BuildingNo, RoomNo, Remark)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    visitor_id,
                    payload.visitor_name,
                    payload.phone,
                    payload.visit_student_id,
                    student["building_no"],
                    student["room_no"],
                    payload.remark,
                ),
            )
        return {"message": "访客已登记", "visitor_id": visitor_id}
    except Exception as exc:
        raise_db(exc)


@router.patch("/visitors/{visitor_id}/leave")
def leave_visitor(
    visitor_id: str,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """记录访客离开时间，将状态更新为"已离开"。"""
    try:
        with connection() as conn:
            conn.cursor().execute(
                """
                UPDATE VisitorRecord
                SET LeaveTime = GETDATE(), Status = N'已离开'
                WHERE VisitorId = ?
                """,
                (visitor_id,),
            )
        return {"message": "访客离开时间已记录"}
    except Exception as exc:
        raise_db(exc)

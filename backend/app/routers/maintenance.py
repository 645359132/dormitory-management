"""
学生宿舍管理系统 - 维修与卫生管理接口
=====================================
提供报修单的提交/查询/更新以及卫生评分的发布/查询。
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..api_utils import new_id, raise_db, student_summary
from ..db import connection, fetch_all, fetch_one
from ..schemas import HygieneCreate, RepairCreate, RepairUpdate
from ..security import CurrentUser, require_admin, require_user


router = APIRouter(tags=["maintenance"])


@router.get("/repairs")
def list_repairs(
    status_filter: str | None = Query(default=None, alias="status"),
    current: CurrentUser = Depends(require_user),
) -> list[dict[str, Any]]:
    """查询报修单列表。

    学生角色：只能看到自己的报修单；
    管理员角色：可按维修状态筛选。
    """
    try:
        conditions = ["1 = 1"]
        params: list[Any] = []
        # 学生仅能查看自己的报修
        if current.role == "student":
            conditions.append("r.StudentId = ?")
            params.append(current.account)
        if status_filter:
            conditions.append("r.Status = ?")
            params.append(status_filter)

        return fetch_all(
            f"""
            SELECT r.RepairId AS repair_id,
                   r.StudentId AS student_id,
                   s.Name AS student_name,
                   r.BuildingNo AS building_no,
                   r.RoomNo AS room_no,
                   r.RepairType AS repair_type,
                   r.FaultDetail AS fault_detail,
                   r.Worker AS worker,
                   r.Fee AS fee,
                   r.Status AS status,
                   r.SubmitTime AS submit_time
            FROM RepairRecord AS r
            LEFT JOIN Student AS s ON s.StudentId = r.StudentId
            WHERE {' AND '.join(conditions)}
            ORDER BY r.SubmitTime DESC
            """,
            tuple(params),
        )
    except Exception as exc:
        raise_db(exc)


@router.post("/repairs")
def create_repair(
    payload: RepairCreate,
    current: CurrentUser = Depends(require_user),
) -> dict[str, str]:
    """提交报修单。

    学生提交时自动使用自己的学号；
    管理员可替指定学生提交（需提供 student_id）。
    报修自动关联到学生所在宿舍。
    """
    try:
        student_id = payload.student_id if current.role == "admin" and payload.student_id else current.account
        repair_id = new_id("R")
        with connection() as conn:
            cursor = conn.cursor()
            # 获取学生的住宿信息
            student = student_summary(cursor, student_id)
            if student["building_no"] is None or student["room_no"] is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="学生尚未分配宿舍")
            cursor.execute(
                """
                INSERT INTO RepairRecord(RepairId, StudentId, BuildingNo, RoomNo, RepairType, FaultDetail, Fee, Status)
                VALUES (?, ?, ?, ?, ?, ?, 0, N'待处理')
                """,
                (
                    repair_id,
                    student_id,
                    student["building_no"],
                    student["room_no"],
                    payload.repair_type,
                    payload.fault_detail,
                ),
            )
        return {"message": "报修单已提交", "repair_id": repair_id}
    except Exception as exc:
        raise_db(exc)


@router.patch("/repairs/{repair_id}")
def update_repair(
    repair_id: str,
    payload: RepairUpdate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """管理员更新报修单：指派维修人、登记费用、更新状态。"""
    try:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            return {"message": "没有变更"}

        field_map = {"worker": "Worker", "fee": "Fee", "status": "Status"}
        sets: list[str] = []
        params: list[Any] = []
        for key, column in field_map.items():
            if key in data:
                sets.append(f"{column} = ?")
                params.append(data[key])

        params.append(repair_id)
        with connection() as conn:
            conn.cursor().execute(f"UPDATE RepairRecord SET {', '.join(sets)} WHERE RepairId = ?", tuple(params))
        return {"message": "报修单已更新"}
    except Exception as exc:
        raise_db(exc)


@router.get("/hygiene")
def list_hygiene(
    building_no: str | None = None,
    room_no: str | None = None,
    current: CurrentUser = Depends(require_user),
) -> list[dict[str, Any]]:
    """查询卫生评分记录。

    学生角色：只能看到自己宿舍的评分；
    管理员角色：可按楼栋和房间筛选。
    """
    try:
        conditions = ["1 = 1"]
        params: list[Any] = []
        if current.role == "student":
            student = fetch_one(
                "SELECT BuildingNo AS building_no, RoomNo AS room_no FROM Student WHERE StudentId = ?",
                (current.account,),
            )
            if student is None or student["building_no"] is None:
                return []
            conditions.extend(["BuildingNo = ?", "RoomNo = ?"])
            params.extend([student["building_no"], student["room_no"]])
        else:
            if building_no:
                conditions.append("BuildingNo = ?")
                params.append(building_no)
            if room_no:
                conditions.append("RoomNo = ?")
                params.append(room_no)

        return fetch_all(
            f"""
            SELECT RecordId AS record_id,
                   BuildingNo AS building_no,
                   RoomNo AS room_no,
                   CheckDate AS check_date,
                   Score AS score,
                   Result AS result
            FROM HygieneRecord
            WHERE {' AND '.join(conditions)}
            ORDER BY CheckDate DESC, RecordId DESC
            """,
            tuple(params),
        )
    except Exception as exc:
        raise_db(exc)


@router.post("/hygiene")
def create_hygiene(
    payload: HygieneCreate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """管理员发布卫生评分记录。

    根据分数自动判定等级：>=90 优，>=80 良，>=60 中，<60 差。
    若不指定检查日期则默认为当天。
    """
    try:
        # 根据分数自动判定卫生等级
        result = "优" if payload.score >= 90 else "良" if payload.score >= 80 else "中" if payload.score >= 60 else "差"
        with connection() as conn:
            conn.cursor().execute(
                """
                INSERT INTO HygieneRecord(BuildingNo, RoomNo, CheckDate, Score, Result)
                VALUES (?, ?, COALESCE(?, CONVERT(DATE, GETDATE())), ?, ?)
                """,
                (payload.building_no, payload.room_no, payload.check_date, payload.score, result),
            )
        return {"message": "卫生记录已发布"}
    except Exception as exc:
        raise_db(exc)

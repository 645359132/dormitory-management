"""
学生宿舍管理系统 - 学生端首页接口
==================================
提供学生端首页的聚合数据，包含个人信息、室友、账单、报修和卫生评分。
"""
from typing import Any

from fastapi import APIRouter, Depends

from ..api_utils import raise_db, student_summary
from ..db import connection, rows_to_dicts
from ..security import CurrentUser, require_student


router = APIRouter(prefix="/student", tags=["student"])


@router.get("/home")
def student_home(current: CurrentUser = Depends(require_student)) -> dict[str, Any]:
    """获取学生端首页的全部数据。

    返回：
    - student: 学生个人信息及宿舍详情
    - roommates: 同宿舍室友列表（学号、姓名、电话）
    - bills: 宿舍账单列表
    - repairs: 个人报修单列表
    - hygiene: 宿舍卫生评分记录
    """
    try:
        with connection() as conn:
            cursor = conn.cursor()
            # 获取学生基本信息
            student = student_summary(cursor, current.account)
            if student["building_no"] is None:
                return {"student": student, "roommates": [], "bills": [], "repairs": [], "hygiene": []}

            room_params = (student["building_no"], student["room_no"])
            # 查询室友
            cursor.execute(
                """
                SELECT StudentId AS student_id, Name AS name, Phone AS phone
                FROM Student
                WHERE BuildingNo = ? AND RoomNo = ?
                ORDER BY StudentId
                """,
                room_params,
            )
            roommates = rows_to_dicts(cursor)

            # 查询宿舍账单
            cursor.execute(
                """
                SELECT BillId AS bill_id,
                       BillMonth AS bill_month,
                       WaterFee AS water_fee,
                       ElectricFee AS electric_fee,
                       TotalAmount AS total_amount,
                       PayStatus AS pay_status
                FROM UtilityBill
                WHERE BuildingNo = ? AND RoomNo = ?
                ORDER BY BillMonth DESC
                """,
                room_params,
            )
            bills = rows_to_dicts(cursor)

            # 查询个人报修单
            cursor.execute(
                """
                SELECT RepairId AS repair_id,
                       RepairType AS repair_type,
                       FaultDetail AS fault_detail,
                       Worker AS worker,
                       Fee AS fee,
                       Status AS status,
                       SubmitTime AS submit_time
                FROM RepairRecord
                WHERE StudentId = ?
                ORDER BY SubmitTime DESC
                """,
                (current.account,),
            )
            repairs = rows_to_dicts(cursor)

            # 查询宿舍卫生评分
            cursor.execute(
                """
                SELECT RecordId AS record_id,
                       CheckDate AS check_date,
                       Score AS score,
                       Result AS result
                FROM HygieneRecord
                WHERE BuildingNo = ? AND RoomNo = ?
                ORDER BY CheckDate DESC, RecordId DESC
                """,
                room_params,
            )
            hygiene = rows_to_dicts(cursor)

        return {
            "student": student,
            "roommates": roommates,
            "bills": bills,
            "repairs": repairs,
            "hygiene": hygiene,
        }
    except Exception as exc:
        raise_db(exc)

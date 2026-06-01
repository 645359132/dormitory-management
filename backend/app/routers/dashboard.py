"""
学生宿舍管理系统 - 管理端数据看板接口
===================================
提供管理员首页的总览数据和统计图表数据。
"""
from typing import Any

from fastapi import APIRouter, Depends

from ..api_utils import raise_db
from ..db import fetch_all, fetch_one
from ..security import CurrentUser, require_admin


router = APIRouter(tags=["dashboard"])


@router.get("/overview")
def overview(_: CurrentUser = Depends(require_admin)) -> dict[str, Any]:
    """获取管理端总览指标。

    包含：学生总数、宿舍间数、床位数、已入住数、未缴账单数和金额、
          待处理维修数、卫生平均分。
    """
    try:
        return fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM Student) AS student_count,
                (SELECT COUNT(*) FROM Dormitory) AS room_count,
                (SELECT ISNULL(SUM(BedTotal), 0) FROM Dormitory) AS bed_count,
                (SELECT ISNULL(SUM(BedUsed), 0) FROM Dormitory) AS occupied_count,
                (SELECT COUNT(*) FROM UtilityBill WHERE PayStatus = N'未缴') AS unpaid_count,
                (SELECT ISNULL(SUM(TotalAmount), 0) FROM UtilityBill WHERE PayStatus = N'未缴') AS unpaid_amount,
                (SELECT COUNT(*) FROM RepairRecord WHERE Status <> N'已完成') AS open_repair_count,
                (SELECT ISNULL(AVG(CAST(Score AS FLOAT)), 0) FROM HygieneRecord) AS hygiene_average
            """
        ) or {}
    except Exception as exc:
        raise_db(exc)


@router.get("/statistics")
def statistics(_: CurrentUser = Depends(require_admin)) -> dict[str, Any]:
    """获取管理端统计数据，包括四个维度的数据。

    返回包含：
    - vacancies: 各宿舍空余床位统计
    - repair_by_type: 维修按类别统计数量和费用
    - hygiene_ranking: 卫生评分排名（前 20）
    - bill_collection: 各月份账单收缴情况
    """
    try:
        return {
            "vacancies": fetch_all(
                """
                SELECT BuildingNo AS building_no,
                       RoomNo AS room_no,
                       BedTotal AS bed_total,
                       BedUsed AS bed_used,
                       BedTotal - BedUsed AS vacant_beds
                FROM Dormitory
                WHERE BedUsed < BedTotal
                ORDER BY vacant_beds DESC, BuildingNo, RoomNo
                """
            ),
            "repair_by_type": fetch_all(
                """
                SELECT RepairType AS repair_type,
                       COUNT(*) AS repair_count,
                       ISNULL(SUM(Fee), 0) AS total_fee
                FROM RepairRecord
                GROUP BY RepairType
                ORDER BY repair_count DESC
                """
            ),
            "hygiene_ranking": fetch_all(
                """
                SELECT TOP 20 BuildingNo AS building_no,
                              RoomNo AS room_no,
                              AVG(CAST(Score AS FLOAT)) AS average_score,
                              COUNT(*) AS check_count,
                              MAX(CheckDate) AS last_check_date
                FROM HygieneRecord
                GROUP BY BuildingNo, RoomNo
                ORDER BY average_score DESC
                """
            ),
            "bill_collection": fetch_all(
                """
                SELECT BillMonth AS bill_month,
                       COUNT(*) AS bill_count,
                       SUM(CASE WHEN PayStatus = N'已缴' THEN 1 ELSE 0 END) AS paid_count,
                       ISNULL(SUM(TotalAmount), 0) AS total_amount
                FROM UtilityBill
                GROUP BY BillMonth
                ORDER BY BillMonth DESC
                """
            ),
        }
    except Exception as exc:
        raise_db(exc)

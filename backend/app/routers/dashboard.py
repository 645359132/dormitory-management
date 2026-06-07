"""
学生宿舍管理系统 - 管理端数据看板接口
===================================
提供管理员首页的总览数据和统计图表数据。
"""
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

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
                (SELECT COUNT(*) FROM Student WHERE BuildingNo IS NULL OR RoomNo IS NULL) AS unassigned_count,
                (SELECT COUNT(*) FROM UtilityBill WHERE PayStatus = N'未缴') AS unpaid_count,
                (SELECT ISNULL(SUM(TotalAmount), 0) FROM UtilityBill WHERE PayStatus = N'未缴') AS unpaid_amount,
                (SELECT COUNT(*) FROM RepairRecord WHERE Status <> N'已完成') AS open_repair_count,
                (SELECT COUNT(*) FROM VisitorRecord WHERE Status = N'在访') AS active_visitor_count,
                (SELECT ISNULL(AVG(CAST(Score AS FLOAT)), 0) FROM HygieneRecord) AS hygiene_average
            """
        ) or {}
    except Exception as exc:
        raise_db(exc)


@router.get("/statistics")
def statistics(
    building_no: str | None = None,
    room_no: str | None = None,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    _: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """获取管理端统计数据，包括四个维度的数据。

    返回包含：
    - vacancies: 各宿舍空余床位统计
    - repair_by_type: 维修按类别统计数量和费用
    - hygiene_ranking: 卫生评分排名（前 20）
    - bill_collection: 各月份账单收缴情况
    """
    try:
        if start_date and end_date and start_date > end_date:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="开始日期不能晚于结束日期")

        room_conditions = ["1 = 1"]
        room_params: list[Any] = []
        repair_conditions = ["1 = 1"]
        repair_params: list[Any] = []
        hygiene_conditions = ["1 = 1"]
        hygiene_params: list[Any] = []
        bill_conditions = ["1 = 1"]
        bill_params: list[Any] = []

        for column, value in (("BuildingNo", building_no), ("RoomNo", room_no)):
            if value:
                room_conditions.append(f"{column} = ?")
                room_params.append(value)
                repair_conditions.append(f"{column} = ?")
                repair_params.append(value)
                hygiene_conditions.append(f"{column} = ?")
                hygiene_params.append(value)
                bill_conditions.append(f"{column} = ?")
                bill_params.append(value)
        if start_date:
            repair_conditions.append("SubmitTime >= ?")
            repair_params.append(start_date)
            hygiene_conditions.append("CheckDate >= ?")
            hygiene_params.append(start_date)
            bill_conditions.append("BillMonth >= ?")
            bill_params.append(start_date.strftime("%Y-%m"))
        if end_date:
            repair_conditions.append("SubmitTime < DATEADD(day, 1, ?)")
            repair_params.append(end_date)
            hygiene_conditions.append("CheckDate <= ?")
            hygiene_params.append(end_date)
            bill_conditions.append("BillMonth <= ?")
            bill_params.append(end_date.strftime("%Y-%m"))

        return {
            "vacancies": fetch_all(
                f"""
                SELECT TOP 6 BuildingNo AS building_no,
                       RoomNo AS room_no,
                       BedTotal AS bed_total,
                       BedUsed AS bed_used,
                       BedTotal - BedUsed AS vacant_beds
                FROM Dormitory
                WHERE BedUsed < BedTotal AND {' AND '.join(room_conditions)}
                ORDER BY vacant_beds DESC, BuildingNo, RoomNo
                """,
                tuple(room_params),
            ),
            "repair_by_type": fetch_all(
                f"""
                SELECT RepairType AS repair_type,
                       COUNT(*) AS repair_count,
                       ISNULL(SUM(Fee), 0) AS total_fee
                FROM RepairRecord
                WHERE {' AND '.join(repair_conditions)}
                GROUP BY RepairType
                ORDER BY repair_count DESC
                """,
                tuple(repair_params),
            ),
            "hygiene_ranking": fetch_all(
                f"""
                SELECT TOP 6 BuildingNo AS building_no,
                              RoomNo AS room_no,
                              AVG(CAST(Score AS FLOAT)) AS average_score,
                              COUNT(*) AS check_count,
                              MAX(CheckDate) AS last_check_date
                FROM HygieneRecord
                WHERE {' AND '.join(hygiene_conditions)}
                GROUP BY BuildingNo, RoomNo
                ORDER BY average_score DESC
                """,
                tuple(hygiene_params),
            ),
            "bill_collection": fetch_all(
                f"""
                SELECT TOP 6 BillMonth AS bill_month,
                       COUNT(*) AS bill_count,
                       SUM(CASE WHEN PayStatus = N'已缴' THEN 1 ELSE 0 END) AS paid_count,
                       ISNULL(SUM(TotalAmount), 0) AS total_amount
                FROM UtilityBill
                WHERE {' AND '.join(bill_conditions)}
                GROUP BY BillMonth
                ORDER BY BillMonth DESC
                """,
                tuple(bill_params),
            ),
        }
    except Exception as exc:
        raise_db(exc)

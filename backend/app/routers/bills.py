"""
学生宿舍管理系统 - 水电账单管理接口
===================================
提供账单的增删改查和缴费操作。
学生只能查看和缴纳自己宿舍的账单，管理员可管理所有账单。
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..api_utils import new_id, raise_db
from ..db import connection, fetch_all, fetch_one
from ..schemas import BillCreate, BillUpdate, PayBillRequest
from ..security import CurrentUser, require_admin, require_user


router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("")
def list_bills(
    bill_month: str | None = None,
    pay_status: str | None = None,
    building_no: str | None = None,
    room_no: str | None = None,
    current: CurrentUser = Depends(require_user),
) -> list[dict[str, Any]]:
    """查询账单列表。

    学生角色：自动限定为本人所在宿舍的账单；
    管理员角色：可按楼栋、房间、月份、缴费状态筛选。
    """
    try:
        conditions = ["1 = 1"]
        params: list[Any] = []
        # 学生用户只能看自己宿舍的账单
        if current.role == "student":
            student = fetch_one(
                "SELECT BuildingNo AS building_no, RoomNo AS room_no FROM Student WHERE StudentId = ?",
                (current.account,),
            )
            if student is None or student["building_no"] is None:
                return []
            conditions.extend(["b.BuildingNo = ?", "b.RoomNo = ?"])
            params.extend([student["building_no"], student["room_no"]])
        else:
            if building_no:
                conditions.append("b.BuildingNo = ?")
                params.append(building_no)
            if room_no:
                conditions.append("b.RoomNo = ?")
                params.append(room_no)
        if bill_month:
            conditions.append("b.BillMonth = ?")
            params.append(bill_month)
        if pay_status:
            conditions.append("b.PayStatus = ?")
            params.append(pay_status)

        return fetch_all(
            f"""
            SELECT b.BillId AS bill_id,
                   b.BuildingNo AS building_no,
                   b.RoomNo AS room_no,
                   b.BillMonth AS bill_month,
                   b.WaterFee AS water_fee,
                   b.ElectricFee AS electric_fee,
                   b.TotalAmount AS total_amount,
                   b.PayStatus AS pay_status
            FROM UtilityBill AS b
            WHERE {' AND '.join(conditions)}
            ORDER BY b.BillMonth DESC, b.BuildingNo, b.RoomNo
            """,
            tuple(params),
        )
    except Exception as exc:
        raise_db(exc)


@router.post("")
def create_bill(
    payload: BillCreate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """管理员创建水电账单，总金额自动计算为水费+电费。"""
    try:
        bill_id = new_id("B")
        with connection() as conn:
            conn.cursor().execute(
                """
                INSERT INTO UtilityBill(BillId, BuildingNo, RoomNo, BillMonth, WaterFee, ElectricFee, TotalAmount, PayStatus)
                VALUES (?, ?, ?, ?, ?, ?, ?, N'未缴')
                """,
                (
                    bill_id,
                    payload.building_no,
                    payload.room_no,
                    payload.bill_month,
                    payload.water_fee,
                    payload.electric_fee,
                    payload.water_fee + payload.electric_fee,
                ),
            )
        return {"message": "账单已生成", "bill_id": bill_id}
    except Exception as exc:
        raise_db(exc)


@router.patch("/{bill_id}")
def update_bill(
    bill_id: str,
    payload: BillUpdate,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """管理员更新账单信息，若修改水费或电费则自动重算总金额。"""
    try:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            return {"message": "没有变更"}

        sets: list[str] = []
        params: list[Any] = []
        if "water_fee" in data:
            sets.append("WaterFee = ?")
            params.append(payload.water_fee)
        if "electric_fee" in data:
            sets.append("ElectricFee = ?")
            params.append(payload.electric_fee)
        if "pay_status" in data:
            sets.append("PayStatus = ?")
            params.append(payload.pay_status)
        if "water_fee" in data or "electric_fee" in data:
            sets.append("TotalAmount = COALESCE(?, WaterFee) + COALESCE(?, ElectricFee)")
            params.extend([payload.water_fee, payload.electric_fee])

        params.append(bill_id)
        with connection() as conn:
            conn.cursor().execute(f"UPDATE UtilityBill SET {', '.join(sets)} WHERE BillId = ?", tuple(params))
        return {"message": "账单已更新"}
    except Exception as exc:
        raise_db(exc)


@router.patch("/{bill_id}/pay")
def pay_bill(
    bill_id: str,
    payload: PayBillRequest,
    current: CurrentUser = Depends(require_user),
) -> dict[str, str]:
    """缴费：将账单状态改为已缴。

    校验：
    - 账单是否存在
    - 账单是否已缴费
    - 缴费金额是否足够
    - 学生只能缴纳自己宿舍的账单
    """
    try:
        with connection() as conn:
            cursor = conn.cursor()
            # 查询账单详情
            cursor.execute(
                """
                SELECT b.TotalAmount, b.PayStatus, b.BuildingNo, b.RoomNo
                FROM UtilityBill AS b
                WHERE b.BillId = ?
                """,
                (bill_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="账单不存在")
            if row.PayStatus == "已缴":
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="账单已缴费")
            if payload.pay_amount < float(row.TotalAmount):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="缴费金额不足")
            # 学生只能缴自己宿舍的账单
            if current.role == "student":
                cursor.execute(
                    """
                    SELECT 1
                    FROM Student
                    WHERE StudentId = ? AND BuildingNo = ? AND RoomNo = ?
                    """,
                    (current.account, row.BuildingNo, row.RoomNo),
                )
                if cursor.fetchone() is None:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="不能缴纳其他宿舍账单")

            cursor.execute("UPDATE UtilityBill SET PayStatus = N'已缴' WHERE BillId = ?", (bill_id,))
        return {"message": "缴费成功"}
    except Exception as exc:
        raise_db(exc)


@router.delete("/{bill_id}")
def delete_bill(
    bill_id: str,
    _: CurrentUser = Depends(require_admin),
) -> dict[str, str]:
    """管理员删除账单。"""
    try:
        with connection() as conn:
            conn.cursor().execute("DELETE FROM UtilityBill WHERE BillId = ?", (bill_id,))
        return {"message": "账单已删除"}
    except Exception as exc:
        raise_db(exc)

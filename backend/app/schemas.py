"""
学生宿舍管理系统 - 请求/响应数据模型（Pydantic Schema）
==================================================
定义所有 API 端点的请求体和响应数据结构，提供自动验证和类型转换。
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ========== 枚举类型常量 ==========

RepairStatus = Literal["待处理", "维修中", "已完成"]  # 维修单状态
RepairType = Literal["水电", "木工", "门窗", "其他"]   # 维修类别
PayStatus = Literal["未缴", "已缴"]                    # 缴费状态
Gender = Literal["男", "女"]                           # 性别
AccountRole = Literal["admin", "student"]              # 账号角色


# ========== 认证相关 ==========

class LoginRequest(BaseModel):
    """登录请求体。"""
    account: str = Field(min_length=1, max_length=20)   # 账号
    password: str = Field(min_length=1, max_length=128)  # 密码


# ========== 宿舍相关 ==========

class DormitoryCreate(BaseModel):
    """创建宿舍请求体。"""
    building_no: str = Field(min_length=1, max_length=10)    # 楼栋编号
    room_no: str = Field(min_length=1, max_length=10)        # 房间号
    bed_total: int = Field(ge=1, le=8)                       # 床位总数
    head_student_id: str | None = Field(default=None, max_length=12)  # 宿舍长学号


class DormitoryUpdate(BaseModel):
    """更新宿舍请求体。"""
    bed_total: int | None = Field(default=None, ge=1, le=8)  # 床位总数
    head_student_id: str | None = Field(default=None, max_length=12)  # 宿舍长学号


# ========== 账号与权限相关 ==========

class AccountCreate(BaseModel):
    """创建登录账号请求体。"""
    account: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=3, max_length=128)
    role: AccountRole


class AccountUpdate(BaseModel):
    """更新登录账号请求体。"""
    password: str | None = Field(default=None, min_length=3, max_length=128)
    role: AccountRole | None = None


# ========== 学生相关 ==========

class StudentCreate(BaseModel):
    """创建学生请求体。"""
    student_id: str = Field(min_length=1, max_length=12)     # 学号
    name: str = Field(min_length=1, max_length=20)            # 姓名
    gender: Gender                                            # 性别
    major: str | None = Field(default=None, max_length=40)    # 专业
    class_name: str | None = Field(default=None, max_length=40)  # 班级
    phone: str | None = Field(default=None, max_length=11)    # 联系电话
    building_no: str | None = Field(default=None, max_length=10)  # 楼栋
    room_no: str | None = Field(default=None, max_length=10)      # 房间号
    move_in_date: date | None = None                          # 入住日期
    password: str | None = Field(default=None, min_length=3, max_length=128)  # 登录密码

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str | None) -> str | None:
        """校验手机号必须为 11 位数字。"""
        if value is not None and (len(value) != 11 or not value.isdigit()):
            raise ValueError("手机号必须为 11 位数字")
        return value


class StudentUpdate(BaseModel):
    """更新学生信息请求体。"""
    name: str | None = Field(default=None, min_length=1, max_length=20)
    gender: Gender | None = None
    major: str | None = Field(default=None, max_length=40)
    class_name: str | None = Field(default=None, max_length=40)
    phone: str | None = Field(default=None, max_length=11)
    building_no: str | None = Field(default=None, max_length=10)
    room_no: str | None = Field(default=None, max_length=10)
    move_in_date: date | None = None

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str | None) -> str | None:
        """校验手机号必须为 11 位数字。"""
        if value is not None and (len(value) != 11 or not value.isdigit()):
            raise ValueError("手机号必须为 11 位数字")
        return value


class PasswordReset(BaseModel):
    """密码重置请求体。"""
    password: str = Field(default="123456", min_length=3, max_length=128)  # 新密码


class StudentBatchImport(BaseModel):
    """批量导入学生请求体。"""
    students: list[StudentCreate] = Field(min_length=1, max_length=500)


# ========== 账单相关 ==========

class BillCreate(BaseModel):
    """创建账单请求体。"""
    building_no: str = Field(min_length=1, max_length=10)    # 楼栋
    room_no: str = Field(min_length=1, max_length=10)        # 房间号
    bill_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")  # 账单月份（格式 YYYY-MM）
    water_fee: float = Field(ge=0)   # 水费
    electric_fee: float = Field(ge=0)  # 电费


class BillUpdate(BaseModel):
    """更新账单请求体。"""
    water_fee: float | None = Field(default=None, ge=0)   # 水费
    electric_fee: float | None = Field(default=None, ge=0)  # 电费
    pay_status: PayStatus | None = None  # 缴费状态


class PayBillRequest(BaseModel):
    """缴费请求体。"""
    pay_amount: float = Field(ge=0)  # 缴费金额


# ========== 维修相关 ==========

class RepairCreate(BaseModel):
    """创建报修单请求体。"""
    repair_type: RepairType                                     # 维修类别
    fault_detail: str | None = Field(default=None, max_length=200)  # 故障描述
    student_id: str | None = Field(default=None, max_length=12)     # 学生学号


class RepairUpdate(BaseModel):
    """更新报修单请求体。"""
    worker: str | None = Field(default=None, max_length=20)  # 维修人
    fee: float | None = Field(default=None, ge=0)            # 维修费用
    status: RepairStatus | None = None                        # 维修状态


# ========== 卫生相关 ==========

class HygieneCreate(BaseModel):
    """创建卫生评分记录请求体。"""
    building_no: str = Field(min_length=1, max_length=10)  # 楼栋
    room_no: str = Field(min_length=1, max_length=10)      # 房间号
    score: int = Field(ge=0, le=100)                       # 卫生评分（0-100）
    check_date: date | None = None                          # 检查日期


# ========== 物品登记相关 ==========

class ItemRecordCreate(BaseModel):
    """创建物品记录请求体。"""
    student_id: str = Field(min_length=1, max_length=12)    # 学生学号
    item_name: str = Field(min_length=1, max_length=50)     # 物品名称
    action: Literal["存入", "取出"]                          # 操作类型
    quantity: int = Field(default=1, ge=1)                  # 数量
    remark: str | None = Field(default=None, max_length=200)  # 备注


class ItemRecordUpdate(BaseModel):
    """更新物品记录请求体。"""
    status: Literal["已登记", "已归还"] | None = None   # 状态
    remark: str | None = Field(default=None, max_length=200)  # 备注


# ========== 访客登记相关 ==========

class VisitorRecordCreate(BaseModel):
    """创建访客记录请求体。"""
    visitor_name: str = Field(min_length=1, max_length=20)     # 访客姓名
    phone: str | None = Field(default=None, max_length=11)     # 联系电话
    visit_student_id: str = Field(min_length=1, max_length=12)  # 被访学生学号
    remark: str | None = Field(default=None, max_length=200)    # 备注

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str | None) -> str | None:
        """校验手机号必须为 11 位数字。"""
        if value is not None and (len(value) != 11 or not value.isdigit()):
            raise ValueError("手机号必须为 11 位数字")
        return value

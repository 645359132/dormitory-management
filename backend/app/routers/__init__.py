"""
学生宿舍管理系统 - 路由聚合模块
=============================
将所有子路由模块注册到统一的 /api 前缀下。
"""
from fastapi import APIRouter

from . import accounts, access, audit, auth, bills, dashboard, dormitories, health, maintenance, student_home, students


# 创建顶层路由，所有 API 路径均以 /api 开头
router = APIRouter(prefix="/api")

# 按顺序注册各功能模块的子路由
for module in (
    health,           # 健康检查
    auth,             # 登录认证
    accounts,         # 账号与权限管理
    dashboard,        # 管理端数据看板
    dormitories,      # 宿舍管理
    students,         # 学生管理
    bills,            # 水电账单管理
    maintenance,      # 维修与卫生管理
    access,           # 出入登记（物品/访客）
    audit,            # 审计日志
    student_home,     # 学生端首页
):
    router.include_router(module.router)

/**
 * 学生宿舍管理系统 - 常量定义模块
 * 定义管理端侧边导航栏的标签页配置。
 */
import type { AdminTab } from './types'

/** 管理端导航标签页列表 */
export const adminTabs: { id: AdminTab; label: string }[] = [
  { id: 'overview', label: '总览' },
  { id: 'residence', label: '学生住宿' },
  { id: 'bills', label: '水电账单' },
  { id: 'maintenance', label: '维修卫生' },
  { id: 'access', label: '出入登记' },
  { id: 'accounts', label: '账号权限' },
]

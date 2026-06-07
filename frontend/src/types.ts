/**
 * 学生宿舍管理系统 - TypeScript 类型定义
 * 定义所有数据模型、表单实体和枚举类型的接口。
 */

/** 用户角色 */
export type Role = 'admin' | 'student' | ''
/** 管理端标签页 ID */
export type AdminTab = 'overview' | 'residence' | 'bills' | 'maintenance' | 'access' | 'accounts'

/** 管理员从总览或列表发起的具体办理事项 */
export interface AdminActionRequest {
  id: number
  name: string
}

/** 服务端分页响应 */
export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 学生名单服务端查询条件 */
export interface StudentQuery {
  q: string
  building_no: string
  residence_status: string
  page: number
  page_size: number
}

// ========== 认证相关 ==========

/** 登录响应 */
export interface LoginResponse {
  token: string    // JWT 令牌
  account: string  // 账号
  role: 'admin' | 'student'  // 角色
}

/** 认证状态（持久化至 localStorage） */
export interface AuthState {
  token: string
  role: Role
  account: string
}

// ========== 数据模型 ==========

/** 管理端总览指标 */
export interface Overview {
  student_count: number      // 学生总数
  room_count: number         // 宿舍间数
  bed_count: number          // 床位总数
  occupied_count: number     // 已入住数
  unassigned_count: number   // 未分配宿舍学生数
  unpaid_count: number       // 未缴账单数
  unpaid_amount: number      // 未缴总额
  open_repair_count: number  // 待处理维修数
  active_visitor_count: number // 当前在访人数
  hygiene_average: number    // 卫生平均分
}

/** 宿舍信息 */
export interface Dormitory {
  building_no: string        // 楼栋
  room_no: string            // 房间号
  bed_total: number          // 床位总数
  bed_used: number           // 已用床位数
  vacant_beds: number        // 空余床位
  head_student_id: string | null  // 宿舍长学号
  head_name: string | null        // 宿舍长姓名
}

/** 学生信息 */
export interface Student {
  student_id: string         // 学号
  name: string               // 姓名
  gender: string             // 性别
  major: string | null       // 专业
  class_name: string | null  // 班级
  phone: string | null       // 联系电话
  building_no: string | null // 楼栋（null 表示未分配）
  room_no: string | null     // 房间号
  move_in_date: string | null // 入住日期
}

/** 水电账单 */
export interface Bill {
  bill_id: string         // 账单号
  building_no?: string    // 楼栋
  room_no?: string        // 房间号
  bill_month: string      // 账单月份
  water_fee: number       // 水费
  electric_fee: number    // 电费
  total_amount: number    // 合计金额
  pay_status: string      // 缴费状态（未缴/已缴）
}

/** 报修记录 */
export interface Repair {
  repair_id: string           // 维修单号
  student_id?: string         // 学生学号
  student_name?: string       // 学生姓名
  building_no?: string        // 楼栋
  room_no?: string            // 房间号
  repair_type: string         // 维修类别
  fault_detail: string | null // 故障描述
  worker: string | null       // 维修人
  fee: number                 // 维修费用
  status: string              // 状态（待处理/维修中/已完成）
  submit_time: string         // 提交时间
}

/** 卫生评分记录 */
export interface Hygiene {
  record_id: number       // 记录 ID
  building_no?: string    // 楼栋
  room_no?: string        // 房间号
  check_date: string      // 检查日期
  score: number           // 评分
  result: string          // 等级（优/良/中/差）
}

/** 管理端统计数据 */
export interface Statistics {
  vacancies: Dormitory[]                                         // 空余床位统计
  repair_by_type: { repair_type: string; repair_count: number; total_fee: number }[]  // 维修按类别统计
  hygiene_ranking: {
    building_no: string
    room_no: string
    average_score: number
    check_count: number
    last_check_date: string
  }[]                                                            // 卫生排名
  bill_collection: { bill_month: string; bill_count: number; paid_count: number; total_amount: number }[]  // 账单收缴统计
}

/** 物品寄存记录 */
export interface ItemRecord {
  item_id: string             // 物品记录 ID
  student_id: string          // 学生学号
  student_name: string | null // 学生姓名
  item_name: string           // 物品名称
  action: string              // 操作（存入/取出）
  quantity: number            // 数量
  status: string              // 状态（已登记/已归还）
  register_time: string       // 登记时间
  remark: string | null       // 备注
}

/** 访客记录 */
export interface VisitorRecord {
  visitor_id: string             // 访客记录 ID
  visitor_name: string           // 访客姓名
  phone: string | null           // 联系电话
  visit_student_id: string       // 被访学生学号
  student_name: string | null    // 被访学生姓名
  building_no: string            // 楼栋
  room_no: string                // 房间号
  enter_time: string             // 进入时间
  leave_time: string | null      // 离开时间
  status: string                 // 状态（在访/已离开）
  remark: string | null          // 备注
}

/** 审计日志 */
export interface AuditLog {
  log_id: number              // 日志 ID
  operator_id: string | null  // 操作人
  action_type: string         // 操作类型
  target_id: string | null    // 目标对象
  detail: string | null       // 详情
  created_at: string          // 创建时间
}

/** 登录账号与角色 */
export interface Account {
  account: string
  role: 'admin' | 'student'
}

/** 学生端首页聚合数据 */
export interface StudentHome {
  student: Student & { bed_total?: number; bed_used?: number; head_student_id?: string | null }
  roommates: Pick<Student, 'student_id' | 'name' | 'phone'>[]  // 室友列表
  bills: Bill[]        // 宿舍账单
  repairs: Repair[]    // 个人报修单
  hygiene: Hygiene[]   // 宿舍卫生评分
}

// ========== 表单实体 ==========

/** 登录表单 */
export interface LoginForm {
  account: string
  password: string
}

/** 新增宿舍表单 */
export interface RoomForm {
  building_no: string    // 楼栋
  room_no: string        // 房间号
  bed_total: number      // 床位数
  head_student_id: string  // 宿舍长学号
}

/** 宿舍编辑表单 */
export interface RoomEditForm extends RoomForm {}

/** 新增学生表单 */
export interface StudentForm {
  student_id: string   // 学号
  name: string         // 姓名
  gender: string       // 性别
  major: string        // 专业
  class_name: string   // 班级
  phone: string        // 电话
  building_no: string  // 楼栋
  room_no: string      // 房间
  move_in_date: string // 入住日期
  password: string     // 初始密码
}

/** 住宿调整表单 */
export interface AssignForm {
  student_id: string   // 学号
  building_no: string  // 目标楼栋
  room_no: string      // 目标房间
  move_in_date: string // 入住日期
}

/** 密码重置表单 */
export interface ResetForm {
  student_id: string  // 学号
  password: string    // 新密码
}

/** 新增账单表单 */
export interface BillForm {
  building_no: string   // 楼栋
  room_no: string       // 房间
  bill_month: string    // 月份
  water_fee: number     // 水费
  electric_fee: number  // 电费
}

/** 账单编辑表单 */
export interface BillEditForm {
  bill_id: string      // 账单号
  water_fee: string    // 新水费
  electric_fee: string // 新电费
  pay_status: string   // 缴费状态
}

/** 报修表单 */
export interface RepairForm {
  repair_type: string   // 维修类别
  fault_detail: string  // 故障详情
  student_id: string    // 学生学号
}

/** 维修处理表单 */
export interface RepairEditForm {
  repair_id: string  // 维修单号
  worker: string     // 维修人
  fee: string        // 费用
  status: string     // 状态
}

/** 卫生评分表单 */
export interface HygieneForm {
  building_no: string  // 楼栋
  room_no: string      // 房间
  score: number        // 分数
  check_date: string   // 检查日期
}

/** 物品登记表单 */
export interface ItemForm {
  student_id: string  // 学号
  item_name: string   // 物品名称
  action: string      // 操作（存入/取出）
  quantity: number    // 数量
  remark: string      // 备注
}

/** 访客登记表单 */
export interface VisitorForm {
  visitor_name: string      // 访客姓名
  phone: string             // 电话
  visit_student_id: string  // 被访学生学号
  remark: string            // 备注
}

/** 账号创建表单 */
export interface AccountForm {
  account: string
  password: string
  role: 'admin' | 'student'
}

/** 账号修改表单 */
export interface AccountEditForm {
  account: string
  password: string
  role: '' | 'admin' | 'student'
}

/** 统计查询条件 */
export interface StatisticsFilters {
  building_no: string
  room_no: string
  start_date: string
  end_date: string
}

/** 账单查询条件 */
export interface BillFilters {
  building_no: string
  room_no: string
  bill_month: string
  pay_status: string
}

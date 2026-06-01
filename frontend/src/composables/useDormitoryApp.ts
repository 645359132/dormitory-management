/**
 * 学生宿舍管理系统 - 全局状态管理与业务逻辑模块
 * 提供所有响应式状态、表单数据和 API 操作方法，作为整个前端应用的核心逻辑层。
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { apiRequest } from '../api'
import type {
  AdminTab,
  AuditLog,
  AuthState,
  Bill,
  BillEditForm,
  BillForm,
  Dormitory,
  Hygiene,
  HygieneForm,
  ItemForm,
  ItemRecord,
  LoginForm,
  LoginResponse,
  Overview,
  Repair,
  RepairEditForm,
  RepairForm,
  ResetForm,
  RoomForm,
  Statistics,
  Student,
  StudentForm,
  StudentHome,
  VisitorForm,
  VisitorRecord,
  AssignForm,
} from '../types'

/**
 * 全局应用状态与业务逻辑组合式函数。
 * 遵循 Vue 3 Composition API 的最佳实践，返回所有可用的状态和方法。
 */
export function useDormitoryApp() {
  // ========== 认证状态（从 localStorage 恢复） ==========

  const auth = reactive<AuthState>({
    token: localStorage.getItem('token') ?? '',
    role: (localStorage.getItem('role') as AuthState['role']) || '',
    account: localStorage.getItem('account') ?? '',
  })

  // ========== UI 状态 ==========

  const loginForm = reactive<LoginForm>({ account: 'admin01', password: 'admin123' })
  const activeTab = ref<AdminTab>('overview')  // 当前激活的管理端标签页
  const loading = ref(false)                    // 全局加载状态
  const error = ref('')                         // 错误消息
  const notice = ref('')                        // 成功通知消息

  // ========== 数据列表（从 API 获取） ==========

  const overview = ref<Overview | null>(null)       // 管理端总览指标
  const statistics = ref<Statistics | null>(null)   // 管理端统计数据
  const dormitories = ref<Dormitory[]>([])          // 宿舍列表
  const students = ref<Student[]>([])               // 学生列表
  const bills = ref<Bill[]>([])                     // 账单列表
  const repairs = ref<Repair[]>([])                 // 报修列表
  const hygiene = ref<Hygiene[]>([])                // 卫生评分列表
  const items = ref<ItemRecord[]>([])               // 物品记录列表
  const visitors = ref<VisitorRecord[]>([])         // 访客记录列表
  const auditLogs = ref<AuditLog[]>([])             // 审计日志列表
  const studentHome = ref<StudentHome | null>(null) // 学生端首页数据

  // ========== 表单数据（双向绑定） ==========

  const roomForm = reactive<RoomForm>({ building_no: '北苑1栋', room_no: '', bed_total: 4, head_student_id: '' })
  const studentForm = reactive<StudentForm>({
    student_id: '',
    name: '',
    gender: '男',
    major: '',
    class_name: '',
    phone: '',
    building_no: '',
    room_no: '',
    password: '123456',
  })
  const assignForm = reactive<AssignForm>({ student_id: '', building_no: '', room_no: '' })
  const resetForm = reactive<ResetForm>({ student_id: '', password: '123456' })
  const billForm = reactive<BillForm>({ building_no: '', room_no: '', bill_month: '2026-06', water_fee: 0, electric_fee: 0 })
  const billEditForm = reactive<BillEditForm>({ bill_id: '', water_fee: '', electric_fee: '', pay_status: '' })
  const repairForm = reactive<RepairForm>({ repair_type: '水电', fault_detail: '', student_id: '' })
  const repairEditForm = reactive<RepairEditForm>({ repair_id: '', worker: '', fee: '', status: '维修中' })
  const hygieneForm = reactive<HygieneForm>({ building_no: '', room_no: '', score: 90, check_date: '' })
  const itemForm = reactive<ItemForm>({ student_id: '', item_name: '', action: '存入', quantity: 1, remark: '' })
  const visitorForm = reactive<VisitorForm>({ visitor_name: '', phone: '', visit_student_id: '', remark: '' })

  // ========== 计算属性 ==========

  /** 入住率（百分比） */
  const occupancyRate = computed(() => {
    if (!overview.value?.bed_count) return 0
    return Math.round((overview.value.occupied_count / overview.value.bed_count) * 100)
  })

  /** 学生端未缴账单数量 */
  const studentUnpaidCount = computed(() => studentHome.value?.bills.filter((bill) => bill.pay_status === '未缴').length ?? 0)

  // ========== 工具函数 ==========

  /** 格式化金额为 CNY 格式 */
  function money(value: number | undefined) {
    return `¥${Number(value ?? 0).toFixed(2)}`
  }

  /** 将空字符串转为 null，用于可选字段的提交处理 */
  function optional(value: string) {
    return value.trim() ? value.trim() : null
  }

  /** 根据状态文本返回对应的 CSS 类名 */
  function statusClass(value: string) {
    if (value === '已缴' || value === '已完成' || value === '已离开' || value === '已归还') return 'ok'
    if (value === '维修中' || value === '在访') return 'warn'
    return 'danger'
  }

  // ========== 内部辅助函数 ==========

  /** 发起带令牌的 API 请求 */
  async function request<T>(path: string, options: RequestInit = {}) {
    return apiRequest<T>(path, auth.token, options)
  }

  /** 统一包装异步操作：自动管理 loading/error/notice 状态 */
  async function run(action: () => Promise<void>) {
    loading.value = true
    error.value = ''
    notice.value = ''
    try {
      await action()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '操作失败'
    } finally {
      loading.value = false
    }
  }

  // ========== 登录与登出 ==========

  /** 提交登录表单，保存令牌到 localStorage 并加载首页数据 */
  async function handleLogin() {
    await run(async () => {
      const result = await apiRequest<LoginResponse>('/api/auth/login', '', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      })
      auth.token = result.token
      auth.role = result.role
      auth.account = result.account
      localStorage.setItem('token', result.token)
      localStorage.setItem('role', result.role)
      localStorage.setItem('account', result.account)
      activeTab.value = 'overview'
      await loadCurrent()
    })
  }

  /** 登出：清除认证信息 */
  function logout() {
    auth.token = ''
    auth.role = ''
    auth.account = ''
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('account')
    studentHome.value = null
  }

  // ========== 数据加载 ==========

  /** 根据当前角色加载对应的首页数据 */
  async function loadCurrent() {
    if (auth.role === 'admin') {
      await loadAdminData()
    } else if (auth.role === 'student') {
      await loadStudentHome()
    }
  }

  /** 加载管理员端全部数据（并行请求） */
  async function loadAdminData() {
    const [overviewData, statisticsData, roomData, studentData, billData, repairData, hygieneData, itemData, visitorData, logData] =
      await Promise.all([
        request<Overview>('/api/overview'),
        request<Statistics>('/api/statistics'),
        request<Dormitory[]>('/api/dormitories'),
        request<Student[]>('/api/students'),
        request<Bill[]>('/api/bills'),
        request<Repair[]>('/api/repairs'),
        request<Hygiene[]>('/api/hygiene'),
        request<ItemRecord[]>('/api/access/items'),
        request<VisitorRecord[]>('/api/access/visitors'),
        request<AuditLog[]>('/api/audit-logs'),
      ])
    overview.value = overviewData
    statistics.value = statisticsData
    dormitories.value = roomData
    students.value = studentData
    bills.value = billData
    repairs.value = repairData
    hygiene.value = hygieneData
    items.value = itemData
    visitors.value = visitorData
    auditLogs.value = logData
  }

  /** 加载学生端首页数据 */
  async function loadStudentHome() {
    studentHome.value = await request<StudentHome>('/api/student/home')
  }

  /** 刷新当前视图数据 */
  async function refresh() {
    await run(loadCurrent)
  }

  // ========== 宿舍管理 ==========

  /** 创建宿舍 */
  async function createRoom() {
    await run(async () => {
      await request('/api/dormitories', {
        method: 'POST',
        body: JSON.stringify({ ...roomForm, head_student_id: optional(roomForm.head_student_id) }),
      })
      notice.value = '宿舍已创建'
      roomForm.room_no = ''
      await loadAdminData()
    })
  }

  /** 删除宿舍 */
  async function deleteRoom(room: Dormitory) {
    await run(async () => {
      await request(`/api/dormitories/${encodeURIComponent(room.building_no)}/${encodeURIComponent(room.room_no)}`, {
        method: 'DELETE',
      })
      notice.value = '宿舍已删除'
      await loadAdminData()
    })
  }

  // ========== 学生管理 ==========

  /** 创建学生 */
  async function createStudent() {
    await run(async () => {
      await request('/api/students', {
        method: 'POST',
        body: JSON.stringify({
          ...studentForm,
          major: optional(studentForm.major),
          class_name: optional(studentForm.class_name),
          phone: optional(studentForm.phone),
          building_no: optional(studentForm.building_no),
          room_no: optional(studentForm.room_no),
        }),
      })
      notice.value = '学生已创建'
      studentForm.student_id = ''
      studentForm.name = ''
      studentForm.phone = ''
      await loadAdminData()
    })
  }

  /** 调整学生住宿（分配 / 退宿） */
  async function assignStudent(clear = false) {
    await run(async () => {
      await request(`/api/students/${encodeURIComponent(assignForm.student_id)}`, {
        method: 'PATCH',
        body: JSON.stringify({
          building_no: clear ? null : optional(assignForm.building_no),
          room_no: clear ? null : optional(assignForm.room_no),
        }),
      })
      notice.value = clear ? '已办理退宿' : '住宿已调整'
      await loadAdminData()
    })
  }

  /** 删除学生 */
  async function deleteStudent(student: Student) {
    await run(async () => {
      await request(`/api/students/${encodeURIComponent(student.student_id)}`, { method: 'DELETE' })
      notice.value = '学生已删除'
      await loadAdminData()
    })
  }

  /** 重置学生密码 */
  async function resetPassword() {
    await run(async () => {
      await request(`/api/students/${encodeURIComponent(resetForm.student_id)}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ password: resetForm.password }),
      })
      notice.value = '密码已重置'
      await loadAdminData()
    })
  }

  // ========== 账单管理 ==========

  /** 创建账单 */
  async function createBill() {
    await run(async () => {
      await request('/api/bills', {
        method: 'POST',
        body: JSON.stringify(billForm),
      })
      notice.value = '账单已生成'
      await loadAdminData()
    })
  }

  /** 更新账单 */
  async function updateBill() {
    await run(async () => {
      const body: Record<string, unknown> = {}
      if (billEditForm.water_fee !== '') body.water_fee = Number(billEditForm.water_fee)
      if (billEditForm.electric_fee !== '') body.electric_fee = Number(billEditForm.electric_fee)
      if (billEditForm.pay_status) body.pay_status = billEditForm.pay_status
      await request(`/api/bills/${encodeURIComponent(billEditForm.bill_id)}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      })
      notice.value = '账单已更新'
      await loadAdminData()
    })
  }

  /** 缴纳账单 */
  async function payBill(bill: Bill) {
    await run(async () => {
      await request(`/api/bills/${encodeURIComponent(bill.bill_id)}/pay`, {
        method: 'PATCH',
        body: JSON.stringify({ pay_amount: bill.total_amount }),
      })
      notice.value = '缴费成功'
      await loadCurrent()
    })
  }

  /** 删除账单 */
  async function deleteBill(bill: Bill) {
    await run(async () => {
      await request(`/api/bills/${encodeURIComponent(bill.bill_id)}`, { method: 'DELETE' })
      notice.value = '账单已删除'
      await loadAdminData()
    })
  }

  // ========== 维修管理 ==========

  /** 提交报修单 */
  async function createRepair() {
    await run(async () => {
      await request('/api/repairs', {
        method: 'POST',
        body: JSON.stringify({
          repair_type: repairForm.repair_type,
          fault_detail: optional(repairForm.fault_detail),
          student_id: optional(repairForm.student_id),
        }),
      })
      notice.value = '报修单已提交'
      repairForm.fault_detail = ''
      await loadCurrent()
    })
  }

  /** 更新报修单（指派维修人/登记费用/更新状态） */
  async function updateRepair() {
    await run(async () => {
      const body: Record<string, unknown> = { status: repairEditForm.status }
      if (repairEditForm.worker) body.worker = repairEditForm.worker
      if (repairEditForm.fee !== '') body.fee = Number(repairEditForm.fee)
      await request(`/api/repairs/${encodeURIComponent(repairEditForm.repair_id)}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      })
      notice.value = '报修单已更新'
      await loadAdminData()
    })
  }

  // ========== 卫生管理 ==========

  /** 发布卫生评分 */
  async function createHygiene() {
    await run(async () => {
      await request('/api/hygiene', {
        method: 'POST',
        body: JSON.stringify({ ...hygieneForm, check_date: optional(hygieneForm.check_date) }),
      })
      notice.value = '卫生记录已发布'
      await loadAdminData()
    })
  }

  // ========== 物品管理 ==========

  /** 登记物品存取 */
  async function createItem() {
    await run(async () => {
      await request('/api/access/items', {
        method: 'POST',
        body: JSON.stringify({ ...itemForm, remark: optional(itemForm.remark) }),
      })
      notice.value = '物品记录已登记'
      itemForm.item_name = ''
      itemForm.remark = ''
      await loadAdminData()
    })
  }

  /** 标记物品已归还 */
  async function returnItem(item: ItemRecord) {
    await run(async () => {
      await request(`/api/access/items/${encodeURIComponent(item.item_id)}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: '已归还' }),
      })
      notice.value = '物品状态已更新'
      await loadAdminData()
    })
  }

  // ========== 访客管理 ==========

  /** 登记访客 */
  async function createVisitor() {
    await run(async () => {
      await request('/api/access/visitors', {
        method: 'POST',
        body: JSON.stringify({ ...visitorForm, phone: optional(visitorForm.phone), remark: optional(visitorForm.remark) }),
      })
      notice.value = '访客已登记'
      visitorForm.visitor_name = ''
      visitorForm.phone = ''
      visitorForm.remark = ''
      await loadAdminData()
    })
  }

  /** 记录访客离开 */
  async function leaveVisitor(visitor: VisitorRecord) {
    await run(async () => {
      await request(`/api/access/visitors/${encodeURIComponent(visitor.visitor_id)}/leave`, { method: 'PATCH' })
      notice.value = '访客离开已记录'
      await loadAdminData()
    })
  }

  // ========== 生命周期 ==========

  // 页面加载时若已登录则自动刷新数据
  onMounted(() => {
    if (auth.token && auth.role) {
      refresh()
    }
  })

  // ========== 导出 ==========

  return {
    // 状态
    activeTab,
    auditLogs,
    auth,
    bills,
    billEditForm,
    billForm,
    dormitories,
    error,
    hygiene,
    hygieneForm,
    itemForm,
    items,
    loading,
    loginForm,
    notice,
    occupancyRate,
    overview,
    repairEditForm,
    repairForm,
    repairs,
    resetForm,
    roomForm,
    assignForm,
    statistics,
    students,
    studentForm,
    studentHome,
    studentUnpaidCount,
    visitorForm,
    visitors,
    // 方法
    assignStudent,
    createBill,
    createHygiene,
    createItem,
    createRepair,
    createRoom,
    createStudent,
    createVisitor,
    deleteBill,
    deleteRoom,
    deleteStudent,
    handleLogin,
    leaveVisitor,
    logout,
    money,
    payBill,
    refresh,
    resetPassword,
    returnItem,
    statusClass,
    updateBill,
    updateRepair,
  }
}

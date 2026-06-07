/**
 * 学生宿舍管理系统 - 全局状态管理与业务逻辑模块
 * 提供所有响应式状态、表单数据和 API 操作方法，作为整个前端应用的核心逻辑层。
 */
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { apiRequest } from '../api'
import type {
  Account,
  AccountEditForm,
  AccountForm,
  AdminTab,
  AuditLog,
  AuthState,
  Bill,
  BillEditForm,
  BillFilters,
  BillForm,
  Dormitory,
  Hygiene,
  HygieneForm,
  ItemForm,
  ItemRecord,
  LoginForm,
  LoginResponse,
  Overview,
  PageResult,
  Repair,
  RepairEditForm,
  RepairForm,
  ResetForm,
  RoomEditForm,
  RoomForm,
  Statistics,
  StatisticsFilters,
  Student,
  StudentForm,
  StudentHome,
  StudentQuery,
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
  const studentTotal = ref(0)                       // 学生查询结果总数
  const studentQueryExecuted = ref(false)           // 是否主动执行过学生查询
  const bills = ref<Bill[]>([])                     // 账单列表
  const repairs = ref<Repair[]>([])                 // 报修列表
  const hygiene = ref<Hygiene[]>([])                // 卫生评分列表
  const items = ref<ItemRecord[]>([])               // 物品记录列表
  const visitors = ref<VisitorRecord[]>([])         // 访客记录列表
  const auditLogs = ref<AuditLog[]>([])             // 审计日志列表
  const accounts = ref<Account[]>([])               // 登录账号列表
  const studentHome = ref<StudentHome | null>(null) // 学生端首页数据

  // ========== 表单数据（双向绑定） ==========

  const roomForm = reactive<RoomForm>({ building_no: '八楼南', room_no: '', bed_total: 4, head_student_id: '' })
  const roomEditForm = reactive<RoomEditForm>({ building_no: '', room_no: '', bed_total: 4, head_student_id: '' })
  const studentForm = reactive<StudentForm>({
    student_id: '',
    name: '',
    gender: '男',
    major: '',
    class_name: '',
    phone: '',
    building_no: '',
    room_no: '',
    move_in_date: '',
    password: '',
  })
  const assignForm = reactive<AssignForm>({ student_id: '', building_no: '', room_no: '', move_in_date: '' })
  const resetForm = reactive<ResetForm>({ student_id: '', password: '123456' })
  const billForm = reactive<BillForm>({ building_no: '', room_no: '', bill_month: '2026-06', water_fee: 0, electric_fee: 0 })
  const billEditForm = reactive<BillEditForm>({ bill_id: '', water_fee: '', electric_fee: '', pay_status: '' })
  const repairForm = reactive<RepairForm>({ repair_type: '水电', fault_detail: '', student_id: '' })
  const repairEditForm = reactive<RepairEditForm>({ repair_id: '', worker: '', fee: '', status: '维修中' })
  const hygieneForm = reactive<HygieneForm>({ building_no: '', room_no: '', score: 90, check_date: '' })
  const itemForm = reactive<ItemForm>({ student_id: '', item_name: '', action: '存入', quantity: 1, remark: '' })
  const visitorForm = reactive<VisitorForm>({ visitor_name: '', phone: '', visit_student_id: '', remark: '' })
  const accountForm = reactive<AccountForm>({ account: '', password: '', role: 'admin' })
  const accountEditForm = reactive<AccountEditForm>({ account: '', password: '', role: '' })
  const statisticsFilters = reactive<StatisticsFilters>({ building_no: '', room_no: '', start_date: '', end_date: '' })
  const billFilters = reactive<BillFilters>({ building_no: '', room_no: '', bill_month: '', pay_status: '' })
  const studentQuery = reactive<StudentQuery>({ q: '', building_no: '', residence_status: '', page: 1, page_size: 10 })

  // ========== 计算属性 ==========

  /** 入住率（百分比） */
  const occupancyRate = computed(() => {
    if (!overview.value?.bed_count) return 0
    return Math.round((overview.value.occupied_count / overview.value.bed_count) * 100)
  })

  /** 学生端未缴账单数量 */
  const studentUnpaidCount = computed(() => studentHome.value?.bills?.filter((bill) => bill.pay_status === '未缴').length ?? 0)

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

  /** 根据非空查询条件生成 API 地址 */
  function queryPath(path: string, values: object) {
    const params = new URLSearchParams()
    Object.entries(values as Record<string, string | number>).forEach(([key, value]) => {
      if (String(value).trim()) params.set(key, String(value).trim())
    })
    const query = params.toString()
    return query ? `${path}?${query}` : path
  }

  function statisticsPath() {
    return queryPath('/api/statistics', statisticsFilters)
  }

  function billsPath() {
    return queryPath('/api/bills', billFilters)
  }

  function studentsPath() {
    return queryPath('/api/students', studentQuery)
  }

  /** 将 CSV 学生名单解析为批量导入请求数据 */
  async function parseStudentCsv(file: File) {
    const rows = (await file.text())
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => line.split(/[\t,，]/).map((value) => value.trim().replace(/^"|"$/g, '')))

    const aliases: Record<string, string> = {
      学号: 'student_id',
      姓名: 'name',
      性别: 'gender',
      专业: 'major',
      班级: 'class_name',
      电话: 'phone',
      联系电话: 'phone',
      楼栋: 'building_no',
      楼宇号: 'building_no',
      房间: 'room_no',
      房间号: 'room_no',
      入住日期: 'move_in_date',
      初始密码: 'password',
    }
    const fallback = ['student_id', 'name', 'gender', 'major', 'class_name', 'phone', 'building_no', 'room_no', 'move_in_date', 'password']
    const first = rows[0] ?? []
    const hasHeader = first.some((value) => Boolean(aliases[value]) || fallback.includes(value))
    const headers = (hasHeader ? first : fallback).map((value) => aliases[value] ?? value)
    const dataRows = hasHeader ? rows.slice(1) : rows

    return dataRows.map((values) => {
      const student: Record<string, string | null> = {}
      headers.forEach((header, index) => {
        student[header] = values[index]?.trim() || null
      })
      return student
    })
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
    students.value = []
    studentTotal.value = 0
    studentQueryExecuted.value = false
  }

  // ========== 数据加载 ==========

  /** 根据当前角色加载对应的首页数据 */
  async function loadCurrent() {
    if (auth.role === 'admin') {
      await loadAdminContext()
    } else if (auth.role === 'student') {
      await loadStudentHome()
    }
  }

  async function loadOverviewMetrics() {
    overview.value = await request<Overview>('/api/overview')
  }

  /** 总览默认只加载汇总指标；统计报表由管理员展开后再查询。 */
  async function loadAdminOverview() {
    await loadOverviewMetrics()
  }

  /** 学生名单由 SQL Server 执行筛选和分页，前端仅保存当前页。 */
  async function refreshStudents() {
    const result = await request<PageResult<Student>>(studentsPath())
    students.value = result.items
    studentTotal.value = result.total
    studentQuery.page = result.page
    studentQueryExecuted.value = true
  }

  /** 切换到具体模块后才加载该模块需要的数据。 */
  async function loadAdminTab(tab: AdminTab) {
    if (tab === 'overview') {
      await loadAdminOverview()
    } else if (tab === 'residence') {
      dormitories.value = await request<Dormitory[]>('/api/dormitories')
      if (studentQueryExecuted.value) await refreshStudents()
    } else if (tab === 'bills') {
      const [billData, roomData] = await Promise.all([request<Bill[]>(billsPath()), request<Dormitory[]>('/api/dormitories')])
      bills.value = billData
      dormitories.value = roomData
    } else if (tab === 'maintenance') {
      const [repairData, hygieneData, roomData] = await Promise.all([
        request<Repair[]>('/api/repairs'),
        request<Hygiene[]>('/api/hygiene'),
        request<Dormitory[]>('/api/dormitories'),
      ])
      repairs.value = repairData
      hygiene.value = hygieneData
      dormitories.value = roomData
    } else if (tab === 'access') {
      const [itemData, visitorData] = await Promise.all([
        request<ItemRecord[]>('/api/access/items'),
        request<VisitorRecord[]>('/api/access/visitors'),
      ])
      items.value = itemData
      visitors.value = visitorData
    } else if (tab === 'accounts') {
      const [logData, accountData] = await Promise.all([
        request<AuditLog[]>('/api/audit-logs'),
        request<Account[]>('/api/accounts'),
      ])
      auditLogs.value = logData
      accounts.value = accountData
    }
  }

  /** 刷新总览和当前模块，不请求其他无关业务数据。 */
  async function loadAdminContext() {
    if (activeTab.value === 'overview') {
      await loadAdminOverview()
      return
    }
    await Promise.all([loadOverviewMetrics(), loadAdminTab(activeTab.value)])
  }

  /** 加载学生端首页数据 */
  async function loadStudentHome() {
    studentHome.value = await request<StudentHome>('/api/student/home')
  }

  /** 刷新当前视图数据 */
  async function refresh() {
    await run(loadCurrent)
  }

  /** 仅刷新统计查询结果 */
  async function refreshStatistics() {
    await run(async () => {
      statistics.value = await request<Statistics>(statisticsPath())
    })
  }

  async function searchStudents() {
    await run(refreshStudents)
  }

  /** 仅刷新账单查询结果 */
  async function refreshBills() {
    await run(async () => {
      bills.value = await request<Bill[]>(billsPath())
    })
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
      await loadAdminContext()
    })
  }

  /** 将宿舍信息填入修改表单 */
  function fillRoomEdit(room: Dormitory) {
    roomEditForm.building_no = room.building_no
    roomEditForm.room_no = room.room_no
    roomEditForm.bed_total = room.bed_total
    roomEditForm.head_student_id = room.head_student_id ?? ''
  }

  /** 修改宿舍床位数或宿舍长 */
  async function updateRoom() {
    await run(async () => {
      await request(`/api/dormitories/${encodeURIComponent(roomEditForm.building_no)}/${encodeURIComponent(roomEditForm.room_no)}`, {
        method: 'PATCH',
        body: JSON.stringify({
          bed_total: roomEditForm.bed_total,
          head_student_id: optional(roomEditForm.head_student_id),
        }),
      })
      notice.value = '宿舍已更新'
      await loadAdminContext()
    })
  }

  /** 删除宿舍 */
  async function deleteRoom(room: Dormitory) {
    await run(async () => {
      await request(`/api/dormitories/${encodeURIComponent(room.building_no)}/${encodeURIComponent(room.room_no)}`, {
        method: 'DELETE',
      })
      notice.value = '宿舍已删除'
      await loadAdminContext()
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
          move_in_date: optional(studentForm.move_in_date),
          password: optional(studentForm.password) ?? studentForm.student_id,
        }),
      })
      notice.value = '学生已创建'
      studentForm.student_id = ''
      studentForm.name = ''
      studentForm.phone = ''
      studentForm.move_in_date = ''
      studentForm.password = ''
      await loadAdminContext()
    })
  }

  /** 从 CSV 文件批量导入学生 */
  async function importStudents(file: File) {
    await run(async () => {
      const studentsToImport = await parseStudentCsv(file)
      await request('/api/students/import', {
        method: 'POST',
        body: JSON.stringify({ students: studentsToImport }),
      })
      notice.value = `已导入 ${studentsToImport.length} 名学生`
      await loadAdminContext()
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
          move_in_date: clear ? null : optional(assignForm.move_in_date),
        }),
      })
      notice.value = clear ? '已办理退宿' : '住宿已调整'
      await loadAdminContext()
    })
  }

  /** 删除学生 */
  async function deleteStudent(student: Student) {
    await run(async () => {
      await request(`/api/students/${encodeURIComponent(student.student_id)}`, { method: 'DELETE' })
      notice.value = '学生已删除'
      await loadAdminContext()
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
      await loadAdminContext()
    })
  }

  // ========== 账号与权限管理 ==========

  /** 创建登录账号 */
  async function createAccount() {
    await run(async () => {
      await request('/api/accounts', {
        method: 'POST',
        body: JSON.stringify(accountForm),
      })
      notice.value = '账号已创建'
      accountForm.account = ''
      accountForm.password = ''
      await loadAdminContext()
    })
  }

  /** 将账号信息填入修改表单 */
  function fillAccountEdit(item: Account) {
    accountEditForm.account = item.account
    accountEditForm.password = ''
    accountEditForm.role = item.role
  }

  /** 修改账号密码或角色 */
  async function updateAccount() {
    await run(async () => {
      const body: Record<string, unknown> = {}
      if (accountEditForm.password) body.password = accountEditForm.password
      if (accountEditForm.role) body.role = accountEditForm.role
      await request(`/api/accounts/${encodeURIComponent(accountEditForm.account)}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      })
      notice.value = '账号已更新'
      accountEditForm.password = ''
      await loadAdminContext()
    })
  }

  /** 删除登录账号 */
  async function deleteAccount(item: Account) {
    await run(async () => {
      await request(`/api/accounts/${encodeURIComponent(item.account)}`, { method: 'DELETE' })
      notice.value = '账号已删除'
      await loadAdminContext()
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
      await loadAdminContext()
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
      await loadAdminContext()
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
      await loadAdminContext()
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
      await loadAdminContext()
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
      await loadAdminContext()
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
      await loadAdminContext()
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
      await loadAdminContext()
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
      await loadAdminContext()
    })
  }

  /** 记录访客离开 */
  async function leaveVisitor(visitor: VisitorRecord) {
    await run(async () => {
      await request(`/api/access/visitors/${encodeURIComponent(visitor.visitor_id)}/leave`, { method: 'PATCH' })
      notice.value = '访客离开已记录'
      await loadAdminContext()
    })
  }

  // ========== 生命周期 ==========

  // 页面加载时若已登录则自动刷新数据
  onMounted(() => {
    if (auth.token && auth.role) {
      refresh()
    }
  })

  watch(activeTab, (tab) => {
    if (auth.role === 'admin') {
      void run(() => loadAdminTab(tab))
    }
  })

  // ========== 导出 ==========

  return {
    // 状态
    accountEditForm,
    accountForm,
    accounts,
    activeTab,
    auditLogs,
    auth,
    bills,
    billEditForm,
    billFilters,
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
    roomEditForm,
    roomForm,
    assignForm,
    statistics,
    statisticsFilters,
    students,
    studentQuery,
    studentQueryExecuted,
    studentTotal,
    studentForm,
    studentHome,
    studentUnpaidCount,
    visitorForm,
    visitors,
    // 方法
    assignStudent,
    createAccount,
    createBill,
    createHygiene,
    createItem,
    createRepair,
    createRoom,
    createStudent,
    createVisitor,
    deleteAccount,
    deleteBill,
    deleteRoom,
    deleteStudent,
    fillAccountEdit,
    fillRoomEdit,
    handleLogin,
    importStudents,
    leaveVisitor,
    logout,
    money,
    payBill,
    refresh,
    refreshBills,
    refreshStatistics,
    searchStudents,
    resetPassword,
    returnItem,
    statusClass,
    updateBill,
    updateRepair,
    updateAccount,
    updateRoom,
  }
}

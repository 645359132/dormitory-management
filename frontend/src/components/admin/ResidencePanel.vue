<!--
  学生宿舍管理系统 - 住宿管理面板
  包含：宿舍学生维护、住宿调整、学生名单导入、密码重置，以及宿舍和学生列表。
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import PaginationBar from '../common/PaginationBar.vue'
import type { AdminActionRequest, AssignForm, Dormitory, ResetForm, RoomEditForm, RoomForm, Student, StudentForm, StudentQuery } from '../../types'

const props = defineProps<{
  actionRequest: AdminActionRequest
  assignForm: AssignForm      // 住宿调整表单
  dormitories: Dormitory[]    // 宿舍列表
  resetForm: ResetForm       // 密码重置表单
  roomEditForm: RoomEditForm // 宿舍编辑表单
  roomForm: RoomForm         // 新增宿舍表单
  studentForm: StudentForm   // 新增学生表单
  students: Student[]        // 学生列表
  studentQuery: StudentQuery  // 服务端查询条件
  studentQueryExecuted: boolean // 是否执行过查询
  studentTotal: number        // 服务端查询结果总数
}>()

const emit = defineEmits<{
  assignStudent: [clear: boolean]       // 调整住宿（clear=true 为退宿）
  createRoom: []                         // 创建宿舍
  createStudent: []                      // 创建学生
  deleteRoom: [room: Dormitory]          // 删除宿舍
  deleteStudent: [student: Student]      // 删除学生
  fillRoomEdit: [room: Dormitory]        // 填充宿舍编辑表单
  importStudents: [file: File]           // 批量导入学生
  recordBill: [room: Dormitory]           // 为宿舍录入水电账单
  recordHygiene: [room: Dormitory]        // 为宿舍录入卫生评分
  resetPassword: []                      // 重置密码
  searchStudents: []                     // 按当前条件查询学生
  updateRoom: []                         // 更新宿舍
}>()

const importFile = ref<File | null>(null)
const activeView = ref<'students' | 'rooms' | 'actions'>('students')
const actionMode = ref<'assign' | 'reset' | 'create-student' | 'create-room' | 'edit-room' | 'import'>('assign')
const roomSearch = ref('')
const roomPage = ref(1)
const roomPageSize = ref(10)

const buildingOptions = computed(() =>
  [...new Set(props.dormitories.map((room) => room.building_no))].sort((a, b) => a.localeCompare(b, 'zh-CN')),
)

const studentPageCount = computed(() => Math.max(1, Math.ceil(props.studentTotal / props.studentQuery.page_size)))

const filteredRooms = computed(() => {
  const query = roomSearch.value.trim().toLowerCase()
  if (!query) return props.dormitories
  return props.dormitories.filter((room) =>
    [room.building_no, room.room_no, room.head_student_id, room.head_name].some((value) => value?.toLowerCase().includes(query)),
  )
})

const roomPageCount = computed(() => Math.max(1, Math.ceil(filteredRooms.value.length / roomPageSize.value)))
const pagedRooms = computed(() => {
  const start = (roomPage.value - 1) * roomPageSize.value
  return filteredRooms.value.slice(start, start + roomPageSize.value)
})

function roomValue(buildingNo: string | null | undefined, roomNo: string | null | undefined) {
  return buildingNo && roomNo ? `${buildingNo}::${roomNo}` : ''
}

function setRoom(value: string, target: { building_no: string; room_no: string }) {
  const [buildingNo = '', roomNo = ''] = value.split('::')
  target.building_no = buildingNo
  target.room_no = roomNo
}

const assignRoom = computed({
  get: () => roomValue(props.assignForm.building_no, props.assignForm.room_no),
  set: (value: string) => setRoom(value, props.assignForm),
})

const studentRoom = computed({
  get: () => roomValue(props.studentForm.building_no, props.studentForm.room_no),
  set: (value: string) => setRoom(value, props.studentForm),
})

watch(roomSearch, () => {
  roomPage.value = 1
})
watch(roomPageSize, () => {
  roomPage.value = 1
})

watch(
  () => props.actionRequest.id,
  () => {
    if (props.actionRequest.name === 'show-unassigned') {
      activeView.value = 'students'
      showUnassignedStudents()
      return
    }
    const modes = ['assign-student', 'create-student', 'create-room', 'import-students']
    if (!modes.includes(props.actionRequest.name)) return
    actionMode.value = props.actionRequest.name === 'assign-student'
      ? 'assign'
      : props.actionRequest.name === 'import-students'
        ? 'import'
        : props.actionRequest.name as 'create-student' | 'create-room'
    activeView.value = 'actions'
  },
  { immediate: true },
)

function openAction(mode: typeof actionMode.value) {
  actionMode.value = mode
  activeView.value = 'actions'
}

function openStudentActions(student: Student, mode: 'assign' | 'reset') {
  props.assignForm.student_id = student.student_id
  props.assignForm.building_no = student.building_no ?? ''
  props.assignForm.room_no = student.room_no ?? ''
  props.assignForm.move_in_date = student.move_in_date ?? ''
  props.resetForm.student_id = student.student_id
  openAction(mode)
}

function openRoomEdit(room: Dormitory) {
  emit('fillRoomEdit', room)
  openAction('edit-room')
}

function selectImportFile(event: Event) {
  importFile.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

function submitImport() {
  if (importFile.value) emit('importStudents', importFile.value)
}

function searchStudents() {
  props.studentQuery.page = 1
  emit('searchStudents')
}

function showUnassignedStudents() {
  props.studentQuery.q = ''
  props.studentQuery.building_no = ''
  props.studentQuery.residence_status = 'unassigned'
  searchStudents()
}

function showAllStudents() {
  props.studentQuery.q = ''
  props.studentQuery.building_no = ''
  props.studentQuery.residence_status = ''
  searchStudents()
}

function changeStudentPage(page: number) {
  props.studentQuery.page = page
  emit('searchStudents')
}

function changeStudentPageSize(pageSize: number) {
  props.studentQuery.page = 1
  props.studentQuery.page_size = pageSize
  emit('searchStudents')
}
</script>

<template>
  <section class="stack">
    <nav class="view-tabs" aria-label="住宿管理视图">
      <button type="button" :class="{ active: activeView === 'students' }" @click="activeView = 'students'">
        学生查询 <span v-if="studentQueryExecuted">{{ studentTotal }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'rooms' }" @click="activeView = 'rooms'">
        宿舍房间 <span>{{ dormitories.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'actions' }" @click="openAction('assign')">业务办理</button>
    </nav>

    <section v-if="activeView === 'students'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>学生名单</h2>
          <p v-if="studentQueryExecuted">共 {{ studentTotal }} 名符合条件，当前仅加载本页</p>
          <p v-else>输入条件后由数据库查询，不默认加载全部学生</p>
        </div>
        <form class="table-filters student-filters" @submit.prevent="searchStudents">
          <input v-model="studentQuery.q" type="search" placeholder="搜索学号、姓名、班级、宿舍" />
          <select v-model="studentQuery.building_no" @change="searchStudents">
            <option value="">全部楼栋</option>
            <option v-for="building in buildingOptions" :key="building">{{ building }}</option>
          </select>
          <select v-model="studentQuery.residence_status" @change="searchStudents">
            <option value="">全部住宿状态</option>
            <option value="assigned">已入住</option>
            <option value="unassigned">未分配</option>
          </select>
          <button class="primary" type="submit">查询</button>
        </form>
      </header>
      <div v-if="studentQueryExecuted" class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>学号</th>
              <th>姓名</th>
              <th>专业 / 班级</th>
              <th>宿舍</th>
              <th>入住日期</th>
              <th>电话</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in students" :key="student.student_id">
              <td class="strong-cell">{{ student.student_id }}</td>
              <td>{{ student.name }}</td>
              <td>{{ student.major || '-' }}<small>{{ student.class_name || '-' }}</small></td>
              <td>
                <span v-if="student.building_no">{{ student.building_no }} {{ student.room_no }}</span>
                <span v-else class="badge warn">未分配</span>
              </td>
              <td>{{ student.move_in_date || '-' }}</td>
              <td>{{ student.phone || '-' }}</td>
              <td class="actions">
                <button type="button" @click="openStudentActions(student, 'assign')">调宿 / 退宿</button>
                <button type="button" @click="openStudentActions(student, 'reset')">重置密码</button>
                <button type="button" class="danger-button" @click="$emit('deleteStudent', student)">删除</button>
              </td>
            </tr>
            <tr v-if="students.length === 0">
              <td class="empty-state" colspan="7">没有符合条件的学生</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="query-prompt">
        <strong>需要查找哪些学生？</strong>
        <p>可按学号、姓名、班级、宿舍或住宿状态查询。全校名单仅在明确需要时分页加载。</p>
        <div>
          <button class="primary" type="button" @click="showUnassignedStudents">查看未分配学生</button>
          <button type="button" @click="showAllStudents">分页查询全部</button>
        </div>
      </div>
      <PaginationBar
        v-if="studentQueryExecuted"
        :page="studentQuery.page"
        :page-count="studentPageCount"
        :page-size="studentQuery.page_size"
        :total="studentTotal"
        @change-page="changeStudentPage"
        @change-page-size="changeStudentPageSize"
      />
    </section>

    <section v-else-if="activeView === 'rooms'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>宿舍房间</h2>
          <p>{{ filteredRooms.length }} 间符合条件</p>
        </div>
        <div class="table-filters compact">
          <input v-model="roomSearch" type="search" placeholder="搜索楼栋、房间、宿舍长" />
        </div>
      </header>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>楼栋</th>
              <th>房间</th>
              <th>床位使用</th>
              <th>空余床位</th>
              <th>宿舍长</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="room in pagedRooms" :key="`${room.building_no}-${room.room_no}`">
              <td class="strong-cell">{{ room.building_no }}</td>
              <td>{{ room.room_no }}</td>
              <td>{{ room.bed_used }}/{{ room.bed_total }}</td>
              <td><span class="badge" :class="room.vacant_beds ? 'ok' : 'danger'">{{ room.vacant_beds }}</span></td>
              <td>{{ room.head_name || room.head_student_id || '-' }}</td>
              <td class="actions">
                <button type="button" @click="$emit('recordBill', room)">录账单</button>
                <button type="button" @click="$emit('recordHygiene', room)">卫生评分</button>
                <button type="button" @click="openRoomEdit(room)">编辑</button>
                <button type="button" class="danger-button" @click="$emit('deleteRoom', room)">删除</button>
              </td>
            </tr>
            <tr v-if="pagedRooms.length === 0">
              <td class="empty-state" colspan="6">没有符合条件的宿舍</td>
            </tr>
          </tbody>
        </table>
      </div>
      <PaginationBar
        :page="roomPage"
        :page-count="roomPageCount"
        :page-size="roomPageSize"
        :total="filteredRooms.length"
        @change-page="roomPage = $event"
        @change-page-size="roomPageSize = $event"
      />
    </section>

    <div v-else class="task-workspace">
      <aside class="task-menu">
        <button type="button" :class="{ active: actionMode === 'assign' }" @click="actionMode = 'assign'">住宿调整</button>
        <button type="button" :class="{ active: actionMode === 'reset' }" @click="actionMode = 'reset'">密码重置</button>
        <button type="button" :class="{ active: actionMode === 'create-student' }" @click="actionMode = 'create-student'">新增学生</button>
        <button type="button" :class="{ active: actionMode === 'create-room' }" @click="actionMode = 'create-room'">新增宿舍</button>
        <button type="button" :class="{ active: actionMode === 'edit-room' }" @click="actionMode = 'edit-room'">修改宿舍</button>
        <button type="button" :class="{ active: actionMode === 'import' }" @click="actionMode = 'import'">导入名单</button>
      </aside>

      <form v-if="actionMode === 'assign'" class="panel labeled-form" @submit.prevent="$emit('assignStudent', false)">
        <header><h2>办理入住 / 调宿 / 退宿</h2><p>从学生名单点击“调宿 / 退宿”可自动带入学号和当前宿舍。</p></header>
        <label>学生学号<input v-model="assignForm.student_id" placeholder="从名单点击办理，或输入学号" required /></label>
        <label>目标宿舍<select v-model="assignRoom"><option value="">暂不分配</option><option v-for="room in dormitories" :key="`${room.building_no}-${room.room_no}`" :disabled="room.vacant_beds <= 0 && roomValue(room.building_no, room.room_no) !== assignRoom" :value="roomValue(room.building_no, room.room_no)">{{ room.building_no }} {{ room.room_no }} · 空余 {{ room.vacant_beds }} 床</option></select></label>
        <label>入住日期<input v-model="assignForm.move_in_date" type="date" /></label>
        <div class="form-actions"><button class="primary" type="submit">确认入住 / 调宿</button><button type="button" class="danger-button" @click="$emit('assignStudent', true)">办理退宿</button></div>
      </form>

      <form v-else-if="actionMode === 'reset'" class="panel labeled-form" @submit.prevent="$emit('resetPassword')">
        <header><h2>学生密码重置</h2><p>重置操作将写入关键操作日志。</p></header>
        <label>学生学号<input v-model="resetForm.student_id" placeholder="从名单点击重置密码，或输入学号" required /></label>
        <label>新密码<input v-model="resetForm.password" placeholder="输入新密码" required /></label>
        <div class="form-actions"><button class="primary" type="submit">确认重置</button></div>
      </form>

      <form v-else-if="actionMode === 'create-student'" class="panel labeled-form wide-form" @submit.prevent="$emit('createStudent')">
        <header><h2>新增学生</h2><p>保存后自动创建学生登录账号；初始密码留空时使用学号。</p></header>
        <label>学号<input v-model="studentForm.student_id" required /></label>
        <label>姓名<input v-model="studentForm.name" required /></label>
        <label>性别<select v-model="studentForm.gender"><option>男</option><option>女</option></select></label>
        <label>专业<input v-model="studentForm.major" /></label>
        <label>班级<input v-model="studentForm.class_name" /></label>
        <label>联系电话<input v-model="studentForm.phone" /></label>
        <label>分配宿舍<select v-model="studentRoom"><option value="">暂不分配</option><option v-for="room in dormitories" :key="`${room.building_no}-${room.room_no}`" :disabled="room.vacant_beds <= 0" :value="roomValue(room.building_no, room.room_no)">{{ room.building_no }} {{ room.room_no }} · 空余 {{ room.vacant_beds }} 床</option></select></label>
        <label>入住日期<input v-model="studentForm.move_in_date" type="date" /></label>
        <label>初始密码<input v-model="studentForm.password" placeholder="留空则使用学号" /></label>
        <div class="form-actions"><button class="primary" type="submit">保存学生</button></div>
      </form>

      <form v-else-if="actionMode === 'create-room'" class="panel labeled-form" @submit.prevent="$emit('createRoom')">
        <header><h2>新增宿舍</h2></header>
        <label>楼栋<input v-model="roomForm.building_no" required /></label>
        <label>房间号<input v-model="roomForm.room_no" required /></label>
        <label>床位数<input v-model.number="roomForm.bed_total" min="1" max="8" type="number" /></label>
        <div class="form-actions"><button class="primary" type="submit">保存宿舍</button></div>
      </form>

      <form v-else-if="actionMode === 'edit-room'" class="panel labeled-form" @submit.prevent="$emit('updateRoom')">
        <header><h2>修改宿舍</h2><p>从宿舍房间列表点击“编辑”可自动带入房间信息。</p></header>
        <label>楼栋<input v-model="roomEditForm.building_no" readonly required /></label>
        <label>房间<input v-model="roomEditForm.room_no" readonly required /></label>
        <label>床位数<input v-model.number="roomEditForm.bed_total" min="1" max="8" type="number" /></label>
        <label>宿舍长学号<input v-model="roomEditForm.head_student_id" placeholder="留空则暂不设置" /></label>
        <div class="form-actions"><button class="primary" type="submit">保存修改</button></div>
      </form>

      <form v-else class="panel labeled-form" @submit.prevent="submitImport">
        <header><h2>学生名单导入</h2><p>导入 CSV 名单，并为学生自动生成登录账号。</p></header>
        <label>CSV 文件<input accept=".csv,text/csv" type="file" required @change="selectImportFile" /></label>
        <div class="form-actions"><button class="primary" type="submit">导入名单</button></div>
      </form>
    </div>
  </section>
</template>

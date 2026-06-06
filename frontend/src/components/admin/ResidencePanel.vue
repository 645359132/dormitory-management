<!--
  学生宿舍管理系统 - 住宿管理面板
  包含：宿舍学生维护、住宿调整、学生名单导入、密码重置，以及宿舍和学生列表。
-->
<script setup lang="ts">
import { ref } from 'vue'
import type { AssignForm, Dormitory, ResetForm, RoomEditForm, RoomForm, Student, StudentForm } from '../../types'

defineProps<{
  assignForm: AssignForm      // 住宿调整表单
  dormitories: Dormitory[]    // 宿舍列表
  resetForm: ResetForm       // 密码重置表单
  roomEditForm: RoomEditForm // 宿舍编辑表单
  roomForm: RoomForm         // 新增宿舍表单
  studentForm: StudentForm   // 新增学生表单
  students: Student[]        // 学生列表
}>()

const emit = defineEmits<{
  assignStudent: [clear: boolean]       // 调整住宿（clear=true 为退宿）
  createRoom: []                         // 创建宿舍
  createStudent: []                      // 创建学生
  deleteRoom: [room: Dormitory]          // 删除宿舍
  deleteStudent: [student: Student]      // 删除学生
  fillRoomEdit: [room: Dormitory]        // 填充宿舍编辑表单
  importStudents: [file: File]           // 批量导入学生
  resetPassword: []                      // 重置密码
  updateRoom: []                         // 更新宿舍
}>()

const importFile = ref<File | null>(null)

function selectImportFile(event: Event) {
  importFile.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

function submitImport() {
  if (importFile.value) emit('importStudents', importFile.value)
}
</script>

<template>
  <section class="stack">
    <!-- 第一行：新增宿舍 + 新增学生 -->
    <div class="content-grid two">
      <form class="panel form-grid" @submit.prevent="$emit('createRoom')">
        <h2>新增宿舍</h2>
        <input v-model="roomForm.building_no" placeholder="楼栋" required />
        <input v-model="roomForm.room_no" placeholder="房间号" required />
        <input v-model.number="roomForm.bed_total" min="1" max="8" type="number" placeholder="床位数" />
        <button class="primary" type="submit">保存宿舍</button>
      </form>

      <form class="panel form-grid" @submit.prevent="$emit('createStudent')">
        <h2>新增学生</h2>
        <input v-model="studentForm.student_id" placeholder="学号" required />
        <input v-model="studentForm.name" placeholder="姓名" required />
        <select v-model="studentForm.gender">
          <option>男</option>
          <option>女</option>
        </select>
        <input v-model="studentForm.major" placeholder="专业" />
        <input v-model="studentForm.class_name" placeholder="班级" />
        <input v-model="studentForm.phone" placeholder="联系电话" />
        <input v-model="studentForm.building_no" placeholder="楼栋" />
        <input v-model="studentForm.room_no" placeholder="房间" />
        <input v-model="studentForm.move_in_date" type="date" />
        <input v-model="studentForm.password" placeholder="初始密码，留空则为学号" />
        <button class="primary" type="submit">保存学生</button>
      </form>
    </div>

    <!-- 第二行：住宿调整 + 密码重置 -->
    <div class="content-grid two">
      <form class="panel inline-form" @submit.prevent="$emit('assignStudent', false)">
        <h2>住宿调整</h2>
        <input v-model="assignForm.student_id" placeholder="学号" required />
        <input v-model="assignForm.building_no" placeholder="楼栋" />
        <input v-model="assignForm.room_no" placeholder="房间" />
        <input v-model="assignForm.move_in_date" type="date" />
        <button class="primary" type="submit">调宿</button>
        <button type="button" @click="$emit('assignStudent', true)">退宿</button>
      </form>

      <form class="panel inline-form" @submit.prevent="$emit('resetPassword')">
        <h2>密码重置</h2>
        <input v-model="resetForm.student_id" placeholder="学号" required />
        <input v-model="resetForm.password" placeholder="新密码" />
        <button class="primary" type="submit">重置</button>
      </form>
    </div>

    <div class="content-grid two">
      <form class="panel inline-form" @submit.prevent="$emit('updateRoom')">
        <h2>修改宿舍</h2>
        <input v-model="roomEditForm.building_no" placeholder="楼栋" readonly required />
        <input v-model="roomEditForm.room_no" placeholder="房间" readonly required />
        <input v-model.number="roomEditForm.bed_total" min="1" max="8" type="number" placeholder="床位数" />
        <input v-model="roomEditForm.head_student_id" placeholder="宿舍长学号" />
        <button class="primary" type="submit">保存修改</button>
      </form>

      <form class="panel inline-form" @submit.prevent="submitImport">
        <h2>学生名单导入</h2>
        <input accept=".csv,text/csv" type="file" required @change="selectImportFile" />
        <button class="primary" type="submit">导入名单</button>
      </form>
    </div>

    <!-- 宿舍房间列表 -->
    <section class="panel table-panel">
      <h2>宿舍房间</h2>
      <table>
        <thead>
          <tr>
            <th>楼栋</th>
            <th>房间</th>
            <th>床位</th>
            <th>宿舍长</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="room in dormitories" :key="`${room.building_no}-${room.room_no}`">
            <td>{{ room.building_no }}</td>
            <td>{{ room.room_no }}</td>
            <td>{{ room.bed_used }}/{{ room.bed_total }}</td>
            <td>{{ room.head_name || room.head_student_id || '-' }}</td>
            <td class="actions">
              <button type="button" @click="$emit('fillRoomEdit', room)">编辑</button>
              <button type="button" @click="$emit('deleteRoom', room)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 学生名单 -->
    <section class="panel table-panel">
      <h2>学生名单</h2>
      <table>
        <thead>
          <tr>
            <th>学号</th>
            <th>姓名</th>
            <th>班级</th>
            <th>宿舍</th>
            <th>入住日期</th>
            <th>电话</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.student_id">
            <td>{{ student.student_id }}</td>
            <td>{{ student.name }}</td>
            <td>{{ student.class_name || '-' }}</td>
            <td>{{ student.building_no ? `${student.building_no} ${student.room_no}` : '未分配' }}</td>
            <td>{{ student.move_in_date || '-' }}</td>
            <td>{{ student.phone || '-' }}</td>
            <td><button type="button" @click="$emit('deleteStudent', student)">删除</button></td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

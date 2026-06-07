<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AdminActionRequest, Dormitory, Hygiene, HygieneForm, Repair, RepairEditForm } from '../../types'

const props = defineProps<{
  actionRequest: AdminActionRequest
  dormitories: Dormitory[]
  hygiene: Hygiene[]
  hygieneForm: HygieneForm
  money: (value: number | undefined) => string
  repairEditForm: RepairEditForm
  repairs: Repair[]
  statusClass: (value: string) => string
}>()

const emit = defineEmits<{
  createHygiene: []
  updateRepair: []
}>()

const activeView = ref<'repairs' | 'hygiene' | 'actions'>('repairs')
const actionMode = ref<'repair' | 'hygiene'>('repair')
const repairStatus = ref('')
const repairSearch = ref('')

const filteredRepairs = computed(() => {
  const query = repairSearch.value.trim().toLowerCase()
  return props.repairs.filter((repair) => {
    const matchesQuery =
      !query ||
      [repair.repair_id, repair.student_id, repair.student_name, repair.building_no, repair.room_no, repair.repair_type, repair.worker]
        .some((value) => value?.toLowerCase().includes(query))
    return matchesQuery && (!repairStatus.value || repair.status === repairStatus.value)
  })
})

const hygieneRoom = computed({
  get: () => props.hygieneForm.building_no && props.hygieneForm.room_no ? `${props.hygieneForm.building_no}::${props.hygieneForm.room_no}` : '',
  set: (value: string) => {
    const [buildingNo = '', roomNo = ''] = value.split('::')
    props.hygieneForm.building_no = buildingNo
    props.hygieneForm.room_no = roomNo
  },
})

watch(
  () => props.actionRequest.id,
  () => {
    if (props.actionRequest.name === 'hygiene') {
      actionMode.value = 'hygiene'
      activeView.value = 'actions'
    } else if (props.actionRequest.name === 'show-open-repairs') {
      repairStatus.value = '待处理'
      activeView.value = 'repairs'
    }
  },
  { immediate: true },
)

function openRepair(repair: Repair) {
  props.repairEditForm.repair_id = repair.repair_id
  props.repairEditForm.worker = repair.worker ?? ''
  props.repairEditForm.fee = String(repair.fee ?? '')
  props.repairEditForm.status = repair.status
  actionMode.value = 'repair'
  activeView.value = 'actions'
}
</script>

<template>
  <section class="stack">
    <nav class="view-tabs" aria-label="维修卫生视图">
      <button type="button" :class="{ active: activeView === 'repairs' }" @click="activeView = 'repairs'">
        维修记录 <span>{{ repairs.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'hygiene' }" @click="activeView = 'hygiene'">
        卫生记录 <span>{{ hygiene.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'actions' }" @click="activeView = 'actions'; actionMode = 'repair'">业务办理</button>
    </nav>

    <section v-if="activeView === 'repairs'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>维修记录</h2>
          <p>{{ filteredRepairs.length }} 条符合条件</p>
        </div>
        <div class="table-filters compact maintenance-filters">
          <input v-model="repairSearch" type="search" placeholder="搜索单号、学生、宿舍、维修人" />
          <select v-model="repairStatus">
            <option value="">全部状态</option>
            <option>待处理</option>
            <option>维修中</option>
            <option>已完成</option>
          </select>
        </div>
      </header>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>单号</th>
              <th>学生</th>
              <th>宿舍</th>
              <th>类别</th>
              <th>故障详情</th>
              <th>状态</th>
              <th>费用</th>
              <th>维修人</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="repair in filteredRepairs" :key="repair.repair_id">
              <td class="strong-cell">{{ repair.repair_id }}</td>
              <td>{{ repair.student_name || repair.student_id }}</td>
              <td>{{ repair.building_no }} {{ repair.room_no }}</td>
              <td>{{ repair.repair_type }}</td>
              <td class="detail-cell">{{ repair.fault_detail || '-' }}</td>
              <td><span class="badge" :class="statusClass(repair.status)">{{ repair.status }}</span></td>
              <td>{{ money(repair.fee) }}</td>
              <td>{{ repair.worker || '-' }}</td>
              <td><button type="button" @click="openRepair(repair)">处理</button></td>
            </tr>
            <tr v-if="filteredRepairs.length === 0"><td class="empty-state" colspan="9">没有符合条件的维修记录</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else-if="activeView === 'hygiene'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>卫生记录</h2>
          <p>共 {{ hygiene.length }} 条</p>
        </div>
      </header>
      <div class="table-scroll">
        <table>
          <thead><tr><th>日期</th><th>宿舍</th><th>分数</th><th>等级</th></tr></thead>
          <tbody>
            <tr v-for="record in hygiene" :key="record.record_id">
              <td>{{ record.check_date }}</td>
              <td class="strong-cell">{{ record.building_no }} {{ record.room_no }}</td>
              <td>{{ record.score }}</td>
              <td><span class="badge ok">{{ record.result }}</span></td>
            </tr>
            <tr v-if="hygiene.length === 0"><td class="empty-state" colspan="4">暂无卫生记录</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-else class="task-workspace">
      <aside class="task-menu">
        <button type="button" :class="{ active: actionMode === 'repair' }" @click="actionMode = 'repair'">维修处理</button>
        <button type="button" :class="{ active: actionMode === 'hygiene' }" @click="actionMode = 'hygiene'">卫生评分</button>
      </aside>

      <form v-if="actionMode === 'repair'" class="panel labeled-form" @submit.prevent="emit('updateRepair')">
        <header><h2>维修指派与结果登记</h2><p>从维修记录点击“处理”可自动带入维修单。</p></header>
        <label>维修单号<input v-model="repairEditForm.repair_id" readonly required /></label>
        <label>维修人<input v-model="repairEditForm.worker" placeholder="输入维修人员" /></label>
        <label>维修费用<input v-model="repairEditForm.fee" type="number" min="0" step="0.01" /></label>
        <label>处理状态<select v-model="repairEditForm.status"><option>待处理</option><option>维修中</option><option>已完成</option></select></label>
        <div class="form-actions"><button class="primary" type="submit">保存处理结果</button></div>
      </form>

      <form v-else class="panel labeled-form" @submit.prevent="emit('createHygiene')">
        <header><h2>发布卫生评分</h2><p>评比等级将根据分数自动计算。</p></header>
        <label>宿舍<select v-model="hygieneRoom" required><option value="">选择宿舍</option><option v-for="room in dormitories" :key="`${room.building_no}-${room.room_no}`" :value="`${room.building_no}::${room.room_no}`">{{ room.building_no }} {{ room.room_no }}</option></select></label>
        <label>卫生分数<input v-model.number="hygieneForm.score" min="0" max="100" type="number" required /></label>
        <label>检查日期<input v-model="hygieneForm.check_date" type="date" /></label>
        <div class="form-actions"><button class="primary" type="submit">发布评分</button></div>
      </form>
    </div>
  </section>
</template>

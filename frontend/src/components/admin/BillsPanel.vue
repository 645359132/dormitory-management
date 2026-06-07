<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import PaginationBar from '../common/PaginationBar.vue'
import type { AdminActionRequest, Bill, BillEditForm, BillFilters, BillForm, Dormitory } from '../../types'

const props = defineProps<{
  actionRequest: AdminActionRequest
  billEditForm: BillEditForm
  billFilters: BillFilters
  billForm: BillForm
  bills: Bill[]
  dormitories: Dormitory[]
  money: (value: number | undefined) => string
  statusClass: (value: string) => string
}>()

const emit = defineEmits<{
  createBill: []
  deleteBill: [bill: Bill]
  payBill: [bill: Bill]
  refreshBills: []
  updateBill: []
}>()

const activeView = ref<'records' | 'actions'>('records')
const actionMode = ref<'create' | 'edit'>('create')
const page = ref(1)
const pageSize = ref(10)
const pageCount = computed(() => Math.max(1, Math.ceil(props.bills.length / pageSize.value)))
const pagedBills = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return props.bills.slice(start, start + pageSize.value)
})

const selectedRoom = computed({
  get: () => props.billForm.building_no && props.billForm.room_no ? `${props.billForm.building_no}::${props.billForm.room_no}` : '',
  set: (value: string) => {
    const [buildingNo = '', roomNo = ''] = value.split('::')
    props.billForm.building_no = buildingNo
    props.billForm.room_no = roomNo
  },
})

watch([() => props.bills.length, pageSize], () => {
  page.value = 1
})

watch(
  () => props.actionRequest.id,
  () => {
    if (props.actionRequest.name === 'create-bill') {
      actionMode.value = 'create'
      activeView.value = 'actions'
    } else if (props.actionRequest.name === 'show-unpaid') {
      props.billFilters.pay_status = '未缴'
      activeView.value = 'records'
      emit('refreshBills')
    }
  },
  { immediate: true },
)

function openEdit(bill: Bill) {
  props.billEditForm.bill_id = bill.bill_id
  props.billEditForm.water_fee = String(bill.water_fee)
  props.billEditForm.electric_fee = String(bill.electric_fee)
  props.billEditForm.pay_status = bill.pay_status
  actionMode.value = 'edit'
  activeView.value = 'actions'
}
</script>

<template>
  <section class="stack">
    <nav class="view-tabs" aria-label="账单管理视图">
      <button type="button" :class="{ active: activeView === 'records' }" @click="activeView = 'records'">
        账单记录 <span>{{ bills.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'actions' }" @click="activeView = 'actions'; actionMode = 'create'">业务办理</button>
    </nav>

    <section v-if="activeView === 'records'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>水电账单</h2>
          <p>{{ bills.length }} 条查询结果</p>
        </div>
        <form class="table-filters bill-filters" @submit.prevent="emit('refreshBills')">
          <input v-model="billFilters.building_no" placeholder="楼栋" />
          <input v-model="billFilters.room_no" placeholder="房间" />
          <input v-model="billFilters.bill_month" aria-label="账单月份" type="month" />
          <select v-model="billFilters.pay_status">
            <option value="">全部状态</option>
            <option>未缴</option>
            <option>已缴</option>
          </select>
          <button class="primary" type="submit">查询</button>
        </form>
      </header>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>账单号</th>
              <th>宿舍</th>
              <th>月份</th>
              <th>水费</th>
              <th>电费</th>
              <th>合计</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="bill in pagedBills" :key="bill.bill_id">
              <td class="strong-cell">{{ bill.bill_id }}</td>
              <td>{{ bill.building_no }} {{ bill.room_no }}</td>
              <td>{{ bill.bill_month }}</td>
              <td>{{ money(bill.water_fee) }}</td>
              <td>{{ money(bill.electric_fee) }}</td>
              <td class="strong-cell">{{ money(bill.total_amount) }}</td>
              <td><span class="badge" :class="statusClass(bill.pay_status)">{{ bill.pay_status }}</span></td>
              <td class="actions">
                <button v-if="bill.pay_status === '未缴'" type="button" @click="emit('payBill', bill)">销账</button>
                <button type="button" @click="openEdit(bill)">编辑</button>
                <button type="button" class="danger-button" @click="emit('deleteBill', bill)">删除</button>
              </td>
            </tr>
            <tr v-if="pagedBills.length === 0"><td class="empty-state" colspan="8">没有符合条件的账单</td></tr>
          </tbody>
        </table>
      </div>
      <PaginationBar
        :page="page"
        :page-count="pageCount"
        :page-size="pageSize"
        :total="bills.length"
        @change-page="page = $event"
        @change-page-size="pageSize = $event"
      />
    </section>

    <div v-else class="task-workspace">
      <aside class="task-menu">
        <button type="button" :class="{ active: actionMode === 'create' }" @click="actionMode = 'create'">录入账单</button>
        <button type="button" :class="{ active: actionMode === 'edit' }" @click="actionMode = 'edit'">修改账单</button>
      </aside>

      <form v-if="actionMode === 'create'" class="panel labeled-form" @submit.prevent="emit('createBill')">
        <header><h2>录入水电账单</h2><p>选择宿舍并录入本月水费、电费，系统自动计算总额。</p></header>
        <label>宿舍<select v-model="selectedRoom" required><option value="">选择宿舍</option><option v-for="room in dormitories" :key="`${room.building_no}-${room.room_no}`" :value="`${room.building_no}::${room.room_no}`">{{ room.building_no }} {{ room.room_no }}</option></select></label>
        <label>账单月份<input v-model="billForm.bill_month" type="month" required /></label>
        <label>水费<input v-model.number="billForm.water_fee" min="0" step="0.01" type="number" required /></label>
        <label>电费<input v-model.number="billForm.electric_fee" min="0" step="0.01" type="number" required /></label>
        <div class="form-actions"><button class="primary" type="submit">生成账单</button></div>
      </form>

      <form v-else class="panel labeled-form" @submit.prevent="emit('updateBill')">
        <header><h2>修改账单</h2><p>从账单记录点击“编辑”可自动带入账单信息。</p></header>
        <label>账单号<input v-model="billEditForm.bill_id" readonly required /></label>
        <label>水费<input v-model="billEditForm.water_fee" type="number" step="0.01" /></label>
        <label>电费<input v-model="billEditForm.electric_fee" type="number" step="0.01" /></label>
        <label>缴费状态<select v-model="billEditForm.pay_status"><option value="">状态不变</option><option>未缴</option><option>已缴</option></select></label>
        <div class="form-actions"><button class="primary" type="submit">保存修改</button></div>
      </form>
    </div>
  </section>
</template>

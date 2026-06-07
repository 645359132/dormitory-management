<!--
  学生宿舍管理系统 - 学生端首页面板
  展示个人指标、室友列表、报修申请、水电账单、报修进度和卫生评比。
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Bill, RepairForm, StudentHome } from '../../types'

const props = defineProps<{
  money: (value: number | undefined) => string   // 金额格式化函数
  repairForm: RepairForm                          // 报修表单
  statusClass: (value: string) => string          // 状态 CSS 类名函数
  studentHome: StudentHome | null                 // 学生首页聚合数据
  unpaidCount: number                             // 未缴账单数量
}>()

defineEmits<{
  createRepair: []              // 提交报修
  payBill: [bill: Bill]         // 缴费
}>()

const activeView = ref<'overview' | 'bills' | 'repairs' | 'hygiene'>('overview')
const unpaidBills = computed(() => props.studentHome?.bills?.filter((bill) => bill.pay_status === '未缴') ?? [])
const openRepairs = computed(() => props.studentHome?.repairs?.filter((repair) => repair.status !== '已完成') ?? [])
const latestHygiene = computed(() => props.studentHome?.hygiene?.[0])
</script>

<template>
  <section class="stack">
    <header class="student-profile">
      <div>
        <span>你好，{{ studentHome?.student.name || '-' }}</span>
        <strong>{{ studentHome?.student.building_no || '尚未分配宿舍' }} {{ studentHome?.student.room_no || '' }}</strong>
      </div>
      <dl>
        <div>
          <dt>学号</dt>
          <dd>{{ studentHome?.student.student_id || '-' }}</dd>
        </div>
        <div>
          <dt>入住日期</dt>
          <dd>{{ studentHome?.student.move_in_date || '-' }}</dd>
        </div>
        <div>
          <dt>宿舍长</dt>
          <dd>{{ studentHome?.student.head_student_id || '-' }}</dd>
        </div>
      </dl>
    </header>

    <nav class="view-tabs" aria-label="学生端视图">
      <button type="button" :class="{ active: activeView === 'overview' }" @click="activeView = 'overview'">概览</button>
      <button type="button" :class="{ active: activeView === 'bills' }" @click="activeView = 'bills'">
        水电账单 <span v-if="unpaidCount">{{ unpaidCount }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'repairs' }" @click="activeView = 'repairs'">
        报修 <span v-if="openRepairs.length">{{ openRepairs.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'hygiene' }" @click="activeView = 'hygiene'">卫生评比</button>
    </nav>

    <div v-if="activeView === 'overview'" class="stack">
      <div class="metric-grid compact-metrics">
        <article class="metric">
          <span>未缴账单</span>
          <strong>{{ unpaidCount }}</strong>
        </article>
        <article class="metric">
          <span>处理中报修</span>
          <strong>{{ openRepairs.length }}</strong>
        </article>
        <article class="metric">
          <span>最近卫生评分</span>
          <strong>{{ latestHygiene?.score ?? '-' }}</strong>
        </article>
      </div>

      <div class="content-grid two">
        <section class="panel table-panel">
          <header class="panel-heading">
            <div>
              <h2>待办事项</h2>
              <p>{{ unpaidBills.length + openRepairs.length }} 项待处理</p>
            </div>
          </header>
          <div v-if="unpaidBills.length || openRepairs.length" class="task-list">
            <button v-for="bill in unpaidBills.slice(0, 3)" :key="bill.bill_id" type="button" @click="activeView = 'bills'">
              <span>水电账单</span>
              <strong>{{ bill.bill_month }} · {{ money(bill.total_amount) }}</strong>
              <small>待缴费</small>
            </button>
            <button v-for="repair in openRepairs.slice(0, 3)" :key="repair.repair_id" type="button" @click="activeView = 'repairs'">
              <span>报修进度</span>
              <strong>{{ repair.repair_type }} · {{ repair.fault_detail || '无详情' }}</strong>
              <small>{{ repair.status }}</small>
            </button>
          </div>
          <p v-else class="empty-state">暂无待办事项</p>
        </section>

        <section class="panel table-panel">
          <header class="panel-heading">
            <div>
              <h2>宿舍成员</h2>
              <p>{{ studentHome?.roommates?.length ?? 0 }} 人</p>
            </div>
          </header>
          <table>
            <tbody>
              <tr v-for="mate in studentHome?.roommates" :key="mate.student_id">
                <td class="strong-cell">{{ mate.name }}</td>
                <td>{{ mate.student_id }}</td>
                <td>{{ mate.phone || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>

    <section v-else-if="activeView === 'bills'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>水电账单</h2>
          <p>{{ studentHome?.bills?.length ?? 0 }} 条记录</p>
        </div>
      </header>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>月份</th>
              <th>水费</th>
              <th>电费</th>
              <th>合计</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="bill in studentHome?.bills" :key="bill.bill_id">
              <td class="strong-cell">{{ bill.bill_month }}</td>
              <td>{{ money(bill.water_fee) }}</td>
              <td>{{ money(bill.electric_fee) }}</td>
              <td>{{ money(bill.total_amount) }}</td>
              <td><span class="badge" :class="statusClass(bill.pay_status)">{{ bill.pay_status }}</span></td>
              <td><button v-if="bill.pay_status === '未缴'" class="primary" type="button" @click="$emit('payBill', bill)">缴费</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-else-if="activeView === 'repairs'" class="content-grid two student-repair-grid">
      <form class="panel form-grid" @submit.prevent="$emit('createRepair')">
        <h2>提交报修</h2>
        <select v-model="repairForm.repair_type">
          <option>水电</option>
          <option>木工</option>
          <option>门窗</option>
          <option>其他</option>
        </select>
        <input v-model="repairForm.fault_detail" placeholder="故障详情" required />
        <button class="primary" type="submit">提交报修</button>
      </form>
      <section class="panel table-panel data-panel">
        <header class="panel-heading">
          <div>
            <h2>报修记录</h2>
            <p>{{ studentHome?.repairs?.length ?? 0 }} 条记录</p>
          </div>
        </header>
        <table>
          <tbody>
            <tr v-for="repair in studentHome?.repairs" :key="repair.repair_id">
              <td class="strong-cell">{{ repair.repair_type }}<small>{{ repair.fault_detail || '-' }}</small></td>
              <td>{{ repair.worker || '待指派' }}</td>
              <td><span class="badge" :class="statusClass(repair.status)">{{ repair.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <section v-else class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>卫生评比</h2>
          <p>{{ studentHome?.hygiene?.length ?? 0 }} 条记录</p>
        </div>
      </header>
      <table>
        <thead>
          <tr>
            <th>检查日期</th>
            <th>得分</th>
            <th>结果</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in studentHome?.hygiene" :key="record.record_id">
            <td>{{ record.check_date }}</td>
            <td class="strong-cell">{{ record.score }}</td>
            <td><span class="badge ok">{{ record.result }}</span></td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

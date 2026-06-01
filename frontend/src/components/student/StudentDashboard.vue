<!--
  学生宿舍管理系统 - 学生端首页面板
  展示个人指标、室友列表、报修申请、水电账单、报修进度和卫生评比。
-->
<script setup lang="ts">
import type { Bill, RepairForm, StudentHome } from '../../types'

defineProps<{
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
</script>

<template>
  <section class="stack">
    <!-- 指标卡片：姓名、宿舍、未缴账单、维修单 -->
    <div class="metric-grid">
      <article class="metric">
        <span>姓名</span>
        <strong>{{ studentHome?.student.name || '-' }}</strong>
      </article>
      <article class="metric">
        <span>宿舍</span>
        <strong>{{ studentHome?.student.building_no || '-' }} {{ studentHome?.student.room_no || '' }}</strong>
      </article>
      <article class="metric">
        <span>未缴账单</span>
        <strong>{{ unpaidCount }}</strong>
      </article>
      <article class="metric">
        <span>维修单</span>
        <strong>{{ studentHome?.repairs.length ?? 0 }}</strong>
      </article>
    </div>

    <!-- 室友列表 + 报修申请 -->
    <div class="content-grid two">
      <section class="panel">
        <h2>室友</h2>
        <table>
          <tbody>
            <tr v-for="mate in studentHome?.roommates" :key="mate.student_id">
              <td>{{ mate.name }}</td>
              <td>{{ mate.student_id }}</td>
              <td>{{ mate.phone || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <form class="panel form-grid" @submit.prevent="$emit('createRepair')">
        <h2>报修申请</h2>
        <select v-model="repairForm.repair_type">
          <option>水电</option>
          <option>木工</option>
          <option>门窗</option>
          <option>其他</option>
        </select>
        <input v-model="repairForm.fault_detail" placeholder="故障详情" />
        <button class="primary" type="submit">提交报修</button>
      </form>
    </div>

    <!-- 水电账单 -->
    <section class="panel table-panel">
      <h2>水电账单</h2>
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
            <td>{{ bill.bill_month }}</td>
            <td>{{ money(bill.water_fee) }}</td>
            <td>{{ money(bill.electric_fee) }}</td>
            <td>{{ money(bill.total_amount) }}</td>
            <td><span class="badge" :class="statusClass(bill.pay_status)">{{ bill.pay_status }}</span></td>
            <td><button v-if="bill.pay_status === '未缴'" type="button" @click="$emit('payBill', bill)">缴费</button></td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 报修进度 + 卫生评比 -->
    <div class="content-grid two">
      <section class="panel table-panel">
        <h2>报修进度</h2>
        <table>
          <tbody>
            <tr v-for="repair in studentHome?.repairs" :key="repair.repair_id">
              <td>{{ repair.repair_type }}</td>
              <td>{{ repair.fault_detail || '-' }}</td>
              <td><span class="badge" :class="statusClass(repair.status)">{{ repair.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel table-panel">
        <h2>卫生评比</h2>
        <table>
          <tbody>
            <tr v-for="record in studentHome?.hygiene" :key="record.record_id">
              <td>{{ record.check_date }}</td>
              <td>{{ record.score }}</td>
              <td><span class="badge ok">{{ record.result }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </section>
</template>

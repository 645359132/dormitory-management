<!--
  学生宿舍管理系统 - 账单管理面板
  包含：录入账单表单、修改账单表单、账单列表。
-->
<script setup lang="ts">
import type { Bill, BillEditForm, BillFilters, BillForm } from '../../types'

defineProps<{
  billEditForm: BillEditForm                       // 账单编辑表单
  billFilters: BillFilters                         // 账单查询条件
  billForm: BillForm                               // 新增账单表单
  bills: Bill[]                                    // 账单列表
  money: (value: number | undefined) => string     // 金额格式化函数
  statusClass: (value: string) => string            // 状态 CSS 类名函数
}>()

defineEmits<{
  createBill: []                 // 生成账单
  deleteBill: [bill: Bill]       // 删除账单
  payBill: [bill: Bill]         // 销账
  refreshBills: []              // 查询账单
  updateBill: []                 // 更新账单
}>()
</script>

<template>
  <section class="stack">
    <!-- 第一行：录入账单 + 修改账单 -->
    <div class="content-grid two">
      <form class="panel form-grid" @submit.prevent="$emit('createBill')">
        <h2>录入账单</h2>
        <input v-model="billForm.building_no" placeholder="楼栋" required />
        <input v-model="billForm.room_no" placeholder="房间" required />
        <input v-model="billForm.bill_month" type="month" required />
        <input v-model.number="billForm.water_fee" min="0" step="0.01" type="number" placeholder="水费" />
        <input v-model.number="billForm.electric_fee" min="0" step="0.01" type="number" placeholder="电费" />
        <button class="primary" type="submit">生成账单</button>
      </form>

      <form class="panel form-grid" @submit.prevent="$emit('updateBill')">
        <h2>修改账单</h2>
        <input v-model="billEditForm.bill_id" placeholder="账单号" required />
        <input v-model="billEditForm.water_fee" type="number" step="0.01" placeholder="新水费" />
        <input v-model="billEditForm.electric_fee" type="number" step="0.01" placeholder="新电费" />
        <select v-model="billEditForm.pay_status">
          <option value="">缴费状态</option>
          <option>未缴</option>
          <option>已缴</option>
        </select>
        <button class="primary" type="submit">更新账单</button>
      </form>
    </div>

    <form class="panel inline-form" @submit.prevent="$emit('refreshBills')">
      <h2>账单查询 / 欠费名单</h2>
      <input v-model="billFilters.building_no" placeholder="楼栋" />
      <input v-model="billFilters.room_no" placeholder="房间" />
      <input v-model="billFilters.bill_month" type="month" />
      <select v-model="billFilters.pay_status">
        <option value="">全部状态</option>
        <option>未缴</option>
        <option>已缴</option>
      </select>
      <button class="primary" type="submit">查询</button>
    </form>

    <!-- 账单列表 -->
    <section class="panel table-panel">
      <h2>账单列表</h2>
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
          <tr v-for="bill in bills" :key="bill.bill_id">
            <td>{{ bill.bill_id }}</td>
            <td>{{ bill.building_no }} {{ bill.room_no }}</td>
            <td>{{ bill.bill_month }}</td>
            <td>{{ money(bill.water_fee) }}</td>
            <td>{{ money(bill.electric_fee) }}</td>
            <td>{{ money(bill.total_amount) }}</td>
            <td><span class="badge" :class="statusClass(bill.pay_status)">{{ bill.pay_status }}</span></td>
            <td class="actions">
              <button v-if="bill.pay_status === '未缴'" type="button" @click="$emit('payBill', bill)">销账</button>
              <button type="button" @click="$emit('deleteBill', bill)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

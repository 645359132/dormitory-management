<!--
  学生宿舍管理系统 - 维修与卫生管理面板
  包含：维修处理表单、卫生评分表单、维修记录列表、卫生记录列表。
-->
<script setup lang="ts">
import type { Hygiene, HygieneForm, Repair, RepairEditForm } from '../../types'

defineProps<{
  hygiene: Hygiene[]                                // 卫生记录列表
  hygieneForm: HygieneForm                          // 卫生评分表单
  money: (value: number | undefined) => string      // 金额格式化函数
  repairEditForm: RepairEditForm                    // 维修处理表单
  repairs: Repair[]                                 // 维修记录列表
  statusClass: (value: string) => string             // 状态 CSS 类名函数
}>()

defineEmits<{
  createHygiene: []    // 发布卫生评分
  updateRepair: []     // 更新维修单
}>()
</script>

<template>
  <section class="stack">
    <!-- 第一行：维修处理 + 卫生评分 -->
    <div class="content-grid two">
      <form class="panel form-grid" @submit.prevent="$emit('updateRepair')">
        <h2>维修处理</h2>
        <input v-model="repairEditForm.repair_id" placeholder="维修单号" required />
        <input v-model="repairEditForm.worker" placeholder="维修人" />
        <input v-model="repairEditForm.fee" type="number" min="0" step="0.01" placeholder="费用" />
        <select v-model="repairEditForm.status">
          <option>待处理</option>
          <option>维修中</option>
          <option>已完成</option>
        </select>
        <button class="primary" type="submit">更新维修单</button>
      </form>

      <form class="panel form-grid" @submit.prevent="$emit('createHygiene')">
        <h2>卫生评分</h2>
        <input v-model="hygieneForm.building_no" placeholder="楼栋" required />
        <input v-model="hygieneForm.room_no" placeholder="房间" required />
        <input v-model.number="hygieneForm.score" min="0" max="100" type="number" placeholder="分数" />
        <input v-model="hygieneForm.check_date" type="date" />
        <button class="primary" type="submit">发布评分</button>
      </form>
    </div>

    <!-- 维修记录列表 -->
    <section class="panel table-panel">
      <h2>维修记录</h2>
      <table>
        <thead>
          <tr>
            <th>单号</th>
            <th>学生</th>
            <th>宿舍</th>
            <th>类别</th>
            <th>状态</th>
            <th>费用</th>
            <th>维修人</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="repair in repairs" :key="repair.repair_id">
            <td>{{ repair.repair_id }}</td>
            <td>{{ repair.student_name || repair.student_id }}</td>
            <td>{{ repair.building_no }} {{ repair.room_no }}</td>
            <td>{{ repair.repair_type }}</td>
            <td><span class="badge" :class="statusClass(repair.status)">{{ repair.status }}</span></td>
            <td>{{ money(repair.fee) }}</td>
            <td>{{ repair.worker || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 卫生记录列表 -->
    <section class="panel table-panel">
      <h2>卫生记录</h2>
      <table>
        <thead>
          <tr>
            <th>日期</th>
            <th>宿舍</th>
            <th>分数</th>
            <th>等级</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in hygiene" :key="record.record_id">
            <td>{{ record.check_date }}</td>
            <td>{{ record.building_no }} {{ record.room_no }}</td>
            <td>{{ record.score }}</td>
            <td><span class="badge ok">{{ record.result }}</span></td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

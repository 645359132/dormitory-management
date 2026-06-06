<!--
  学生宿舍管理系统 - 管理员总览面板
  展示核心指标卡片 + 空余床位、水电收缴、卫生排名数据面板。
-->
<script setup lang="ts">
import type { Overview, Statistics, StatisticsFilters } from '../../types'

defineProps<{
  filters: StatisticsFilters                       // 查询条件
  money: (value: number | undefined) => string  // 金额格式化函数
  occupancyRate: number                           // 入住率
  overview: Overview | null                       // 总览指标
  statistics: Statistics | null                   // 统计数据
}>()

defineEmits<{
  refreshStats: []
}>()
</script>

<template>
  <section class="stack">
    <!-- 指标卡片：学生数、入住率、未缴账单、待处理维修 -->
    <div class="metric-grid">
      <article class="metric">
        <span>学生</span>
        <strong>{{ overview?.student_count ?? 0 }}</strong>
      </article>
      <article class="metric">
        <span>入住率</span>
        <strong>{{ occupancyRate }}%</strong>
      </article>
      <article class="metric">
        <span>未缴账单</span>
        <strong>{{ overview?.unpaid_count ?? 0 }}</strong>
      </article>
      <article class="metric">
        <span>待处理维修</span>
        <strong>{{ overview?.open_repair_count ?? 0 }}</strong>
      </article>
    </div>

    <form class="panel inline-form" @submit.prevent="$emit('refreshStats')">
      <h2>统计查询</h2>
      <input v-model="filters.building_no" placeholder="楼栋" />
      <input v-model="filters.room_no" placeholder="房间" />
      <input v-model="filters.start_date" type="date" />
      <input v-model="filters.end_date" type="date" />
      <button class="primary" type="submit">查询</button>
    </form>

    <!-- 查询统计结果 -->
    <div class="content-grid two">
      <section class="panel">
        <h2>空余床位</h2>
        <table>
          <tbody>
            <tr v-for="room in statistics?.vacancies.slice(0, 8)" :key="`${room.building_no}-${room.room_no}`">
              <td>{{ room.building_no }} {{ room.room_no }}</td>
              <td>{{ room.vacant_beds }} 空床</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel">
        <h2>水电收缴</h2>
        <table>
          <tbody>
            <tr v-for="row in statistics?.bill_collection.slice(0, 6)" :key="row.bill_month">
              <td>{{ row.bill_month }}</td>
              <td>{{ row.paid_count }}/{{ row.bill_count }}</td>
              <td>{{ money(row.total_amount) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel">
        <h2>卫生排名</h2>
        <table>
          <tbody>
            <tr v-for="row in statistics?.hygiene_ranking.slice(0, 6)" :key="`${row.building_no}-${row.room_no}`">
              <td>{{ row.building_no }} {{ row.room_no }}</td>
              <td>{{ row.average_score.toFixed(1) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel">
        <h2>维修统计</h2>
        <table>
          <tbody>
            <tr v-for="row in statistics?.repair_by_type" :key="row.repair_type">
              <td>{{ row.repair_type }}</td>
              <td>{{ row.repair_count }} 单</td>
              <td>{{ money(row.total_fee) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </section>
</template>

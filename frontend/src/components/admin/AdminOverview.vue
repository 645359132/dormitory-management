<script setup lang="ts">
import type { AdminTab, Overview, Statistics, StatisticsFilters } from '../../types'

defineProps<{
  filters: StatisticsFilters
  money: (value: number | undefined) => string
  occupancyRate: number
  overview: Overview | null
  statistics: Statistics | null
}>()

defineEmits<{
  navigate: [tab: AdminTab]
  openAction: [tab: AdminTab, action: string]
  refreshStats: []
}>()
</script>

<template>
  <section class="stack">
    <section class="quick-actions">
      <div>
        <span>常用办理</span>
        <small>直接进入对应表单</small>
      </div>
      <button type="button" @click="$emit('openAction', 'residence', 'assign-student')">办理入住 / 调宿</button>
      <button type="button" @click="$emit('openAction', 'residence', 'create-student')">新增学生</button>
      <button type="button" @click="$emit('openAction', 'bills', 'create-bill')">录入水电账单</button>
      <button type="button" @click="$emit('openAction', 'maintenance', 'hygiene')">录入卫生评分</button>
      <button type="button" @click="$emit('openAction', 'access', 'visitor')">登记访客</button>
    </section>

    <section class="panel work-queue">
      <header>
        <div>
          <h2>待办工作</h2>
          <p>只展示需要管理员处理的事项</p>
        </div>
        <div class="operation-facts">
          <span>学生 {{ overview?.student_count ?? 0 }}</span>
          <span>宿舍 {{ overview?.room_count ?? 0 }}</span>
          <span>入住率 {{ occupancyRate }}%</span>
          <span>卫生均分 {{ overview?.hygiene_average?.toFixed(1) ?? '0.0' }}</span>
        </div>
      </header>
      <div class="work-queue-list">
        <button type="button" @click="$emit('openAction', 'residence', 'show-unassigned')">
          <strong>{{ overview?.unassigned_count ?? 0 }}</strong>
          <span>名学生尚未分配宿舍</span>
          <small>查询并办理入住</small>
        </button>
        <button type="button" @click="$emit('openAction', 'bills', 'show-unpaid')">
          <strong>{{ overview?.unpaid_count ?? 0 }}</strong>
          <span>笔水电账单尚未缴纳</span>
          <small>{{ money(overview?.unpaid_amount) }} 待收缴</small>
        </button>
        <button type="button" @click="$emit('openAction', 'maintenance', 'show-open-repairs')">
          <strong>{{ overview?.open_repair_count ?? 0 }}</strong>
          <span>项维修尚未完成</span>
          <small>安排人员或登记结果</small>
        </button>
        <button type="button" @click="$emit('openAction', 'access', 'show-active-visitors')">
          <strong>{{ overview?.active_visitor_count ?? 0 }}</strong>
          <span>名访客当前仍在访</span>
          <small>登记离开状态</small>
        </button>
      </div>
    </section>

    <details class="overview-details" @toggle="($event.currentTarget as HTMLDetailsElement).open && $emit('refreshStats')">
      <summary>查询统计报表</summary>
      <section class="panel overview-report">
      <header class="report-toolbar">
        <div>
          <h2>运营统计</h2>
          <p>按楼栋、房间或日期查看当前统计结果</p>
        </div>
        <form class="report-filters" @submit.prevent="$emit('refreshStats')">
          <input v-model="filters.building_no" placeholder="楼栋" />
          <input v-model="filters.room_no" placeholder="房间" />
          <input v-model="filters.start_date" aria-label="开始日期" type="date" />
          <input v-model="filters.end_date" aria-label="结束日期" type="date" />
          <button class="primary" type="submit">查询</button>
        </form>
      </header>

      <div class="overview-report-grid">
        <section class="report-block">
          <header>
            <h2>空余床位</h2>
            <button type="button" @click="$emit('navigate', 'residence')">查看全部</button>
          </header>
          <table>
            <tbody>
              <tr v-for="room in statistics?.vacancies.slice(0, 6)" :key="`${room.building_no}-${room.room_no}`">
                <td class="strong-cell">{{ room.building_no }} {{ room.room_no }}</td>
                <td><span class="badge ok">{{ room.vacant_beds }} 空床</span></td>
              </tr>
              <tr v-if="!statistics?.vacancies.length"><td class="empty-state">暂无空余床位</td></tr>
            </tbody>
          </table>
        </section>

        <section class="report-block">
          <header>
            <h2>水电收缴</h2>
            <button type="button" @click="$emit('navigate', 'bills')">处理账单</button>
          </header>
          <table>
            <tbody>
              <tr v-for="row in statistics?.bill_collection.slice(0, 6)" :key="row.bill_month">
                <td class="strong-cell">{{ row.bill_month }}</td>
                <td>{{ row.paid_count }}/{{ row.bill_count }} 已缴</td>
                <td>{{ money(row.total_amount) }}</td>
              </tr>
              <tr v-if="!statistics?.bill_collection.length"><td class="empty-state">暂无账单统计</td></tr>
            </tbody>
          </table>
        </section>

        <section class="report-block">
          <header>
            <h2>卫生排名</h2>
            <button type="button" @click="$emit('navigate', 'maintenance')">查看记录</button>
          </header>
          <table>
            <tbody>
              <tr v-for="(row, index) in statistics?.hygiene_ranking.slice(0, 6)" :key="`${row.building_no}-${row.room_no}`">
                <td class="rank-cell">{{ index + 1 }}</td>
                <td class="strong-cell">{{ row.building_no }} {{ row.room_no }}</td>
                <td>{{ row.average_score.toFixed(1) }}</td>
              </tr>
              <tr v-if="!statistics?.hygiene_ranking.length"><td class="empty-state">暂无卫生评分</td></tr>
            </tbody>
          </table>
        </section>

        <section class="report-block">
          <header>
            <h2>维修分类</h2>
            <button type="button" @click="$emit('navigate', 'maintenance')">处理维修</button>
          </header>
          <table>
            <tbody>
              <tr v-for="row in statistics?.repair_by_type" :key="row.repair_type">
                <td class="strong-cell">{{ row.repair_type }}</td>
                <td>{{ row.repair_count }} 单</td>
                <td>{{ money(row.total_fee) }}</td>
              </tr>
              <tr v-if="!statistics?.repair_by_type.length"><td class="empty-state">暂无维修记录</td></tr>
            </tbody>
          </table>
        </section>
      </div>
      </section>
    </details>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AdminActionRequest, ItemForm, ItemRecord, VisitorForm, VisitorRecord } from '../../types'

const props = defineProps<{
  actionRequest: AdminActionRequest
  itemForm: ItemForm
  items: ItemRecord[]
  statusClass: (value: string) => string
  visitorForm: VisitorForm
  visitors: VisitorRecord[]
}>()

const emit = defineEmits<{
  createItem: []
  createVisitor: []
  leaveVisitor: [visitor: VisitorRecord]
  returnItem: [item: ItemRecord]
}>()

const activeView = ref<'visitors' | 'items' | 'register'>('visitors')
const registerMode = ref<'visitor' | 'item'>('visitor')
const search = ref('')
const activeOnly = ref(false)

const filteredVisitors = computed(() => {
  const query = search.value.trim().toLowerCase()
  return props.visitors.filter((visitor) => {
    const matchesQuery =
      !query ||
      [visitor.visitor_name, visitor.phone, visitor.visit_student_id, visitor.student_name, visitor.building_no, visitor.room_no]
        .some((value) => value?.toLowerCase().includes(query))
    return matchesQuery && (!activeOnly.value || visitor.status === '在访')
  })
})

const filteredItems = computed(() => {
  const query = search.value.trim().toLowerCase()
  return props.items.filter((item) => {
    const matchesQuery = !query || [item.student_id, item.student_name, item.item_name].some((value) => value?.toLowerCase().includes(query))
    return matchesQuery && (!activeOnly.value || item.status !== '已归还')
  })
})

watch(
  () => props.actionRequest.id,
  () => {
    if (props.actionRequest.name === 'show-active-visitors') {
      activeOnly.value = true
      activeView.value = 'visitors'
      return
    }
    if (!['visitor', 'item'].includes(props.actionRequest.name)) return
    registerMode.value = props.actionRequest.name as 'visitor' | 'item'
    activeView.value = 'register'
  },
  { immediate: true },
)
</script>

<template>
  <section class="stack">
    <nav class="view-tabs" aria-label="出入登记视图">
      <button type="button" :class="{ active: activeView === 'visitors' }" @click="activeView = 'visitors'">
        访客记录 <span>{{ visitors.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'items' }" @click="activeView = 'items'">
        物品记录 <span>{{ items.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'register' }" @click="activeView = 'register'; registerMode = 'visitor'">登记办理</button>
    </nav>

    <section v-if="activeView !== 'register'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>{{ activeView === 'visitors' ? '访客记录' : '物品记录' }}</h2>
          <p>{{ activeView === 'visitors' ? filteredVisitors.length : filteredItems.length }} 条符合条件</p>
        </div>
        <div class="record-toolbar">
          <input v-model="search" type="search" :placeholder="activeView === 'visitors' ? '搜索访客、学生、宿舍' : '搜索学生、物品'" />
          <label class="check-control">
            <input v-model="activeOnly" type="checkbox" />
            <span>{{ activeView === 'visitors' ? '仅看在访' : '仅看未归还' }}</span>
          </label>
        </div>
      </header>

      <div v-if="activeView === 'visitors'" class="table-scroll">
        <table>
          <thead><tr><th>访客</th><th>联系电话</th><th>被访学生</th><th>宿舍</th><th>进入时间</th><th>状态</th><th></th></tr></thead>
          <tbody>
            <tr v-for="visitor in filteredVisitors" :key="visitor.visitor_id">
              <td class="strong-cell">{{ visitor.visitor_name }}</td>
              <td>{{ visitor.phone || '-' }}</td>
              <td>{{ visitor.student_name || visitor.visit_student_id }}<small>{{ visitor.visit_student_id }}</small></td>
              <td>{{ visitor.building_no }} {{ visitor.room_no }}</td>
              <td>{{ visitor.enter_time }}</td>
              <td><span class="badge" :class="statusClass(visitor.status)">{{ visitor.status }}</span></td>
              <td><button v-if="visitor.status === '在访'" type="button" @click="emit('leaveVisitor', visitor)">登记离开</button></td>
            </tr>
            <tr v-if="filteredVisitors.length === 0"><td class="empty-state" colspan="7">没有符合条件的访客记录</td></tr>
          </tbody>
        </table>
      </div>

      <div v-else class="table-scroll">
        <table>
          <thead><tr><th>学生</th><th>物品</th><th>操作</th><th>数量</th><th>登记时间</th><th>状态</th><th></th></tr></thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.item_id">
              <td class="strong-cell">{{ item.student_name || item.student_id }}<small>{{ item.student_id }}</small></td>
              <td>{{ item.item_name }}</td>
              <td>{{ item.action }}</td>
              <td>{{ item.quantity }}</td>
              <td>{{ item.register_time }}</td>
              <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
              <td><button v-if="item.status !== '已归还'" type="button" @click="emit('returnItem', item)">登记归还</button></td>
            </tr>
            <tr v-if="filteredItems.length === 0"><td class="empty-state" colspan="7">没有符合条件的物品记录</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-else class="task-workspace">
      <aside class="task-menu">
        <button type="button" :class="{ active: registerMode === 'visitor' }" @click="registerMode = 'visitor'">访客登记</button>
        <button type="button" :class="{ active: registerMode === 'item' }" @click="registerMode = 'item'">物品登记</button>
      </aside>

      <form v-if="registerMode === 'visitor'" class="panel labeled-form" @submit.prevent="emit('createVisitor')">
        <header><h2>访客进入登记</h2><p>输入学号时可从现有学生中选择，宿舍信息将自动关联。</p></header>
        <label>访客姓名<input v-model="visitorForm.visitor_name" required /></label>
        <label>联系电话<input v-model="visitorForm.phone" /></label>
        <label>被访学生学号<input v-model="visitorForm.visit_student_id" required /></label>
        <label>备注<input v-model="visitorForm.remark" /></label>
        <div class="form-actions"><button class="primary" type="submit">登记进入</button></div>
      </form>

      <form v-else class="panel labeled-form" @submit.prevent="emit('createItem')">
        <header><h2>大件物品登记</h2></header>
        <label>学生学号<input v-model="itemForm.student_id" required /></label>
        <label>物品名称<input v-model="itemForm.item_name" required /></label>
        <label>登记操作<select v-model="itemForm.action"><option>存入</option><option>取出</option></select></label>
        <label>数量<input v-model.number="itemForm.quantity" type="number" min="1" required /></label>
        <label>备注<input v-model="itemForm.remark" /></label>
        <div class="form-actions"><button class="primary" type="submit">登记物品</button></div>
      </form>
    </div>
  </section>
</template>

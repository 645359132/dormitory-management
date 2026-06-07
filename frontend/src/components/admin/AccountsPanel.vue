<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import PaginationBar from '../common/PaginationBar.vue'
import type { Account, AccountEditForm, AccountForm, AuditLog } from '../../types'

const props = defineProps<{
  accountEditForm: AccountEditForm
  accountForm: AccountForm
  accounts: Account[]
  auditLogs: AuditLog[]
}>()

const emit = defineEmits<{
  createAccount: []
  deleteAccount: [account: Account]
  fillAccountEdit: [account: Account]
  updateAccount: []
}>()

const activeView = ref<'accounts' | 'logs' | 'actions'>('accounts')
const search = ref('')
const role = ref('')
const page = ref(1)
const pageSize = ref(10)

const filteredAccounts = computed(() => {
  const query = search.value.trim().toLowerCase()
  return props.accounts.filter((item) => (!query || item.account.toLowerCase().includes(query)) && (!role.value || item.role === role.value))
})
const pageCount = computed(() => Math.max(1, Math.ceil(filteredAccounts.value.length / pageSize.value)))
const pagedAccounts = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredAccounts.value.slice(start, start + pageSize.value)
})

watch([search, role, pageSize], () => {
  page.value = 1
})

function openEdit(account: Account) {
  emit('fillAccountEdit', account)
  activeView.value = 'actions'
}
</script>

<template>
  <section class="stack">
    <nav class="view-tabs" aria-label="账号权限视图">
      <button type="button" :class="{ active: activeView === 'accounts' }" @click="activeView = 'accounts'">
        账号列表 <span>{{ accounts.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'logs' }" @click="activeView = 'logs'">
        操作日志 <span>{{ auditLogs.length }}</span>
      </button>
      <button type="button" :class="{ active: activeView === 'actions' }" @click="activeView = 'actions'">账号办理</button>
    </nav>

    <section v-if="activeView === 'accounts'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>账号列表</h2>
          <p>{{ filteredAccounts.length }} 个账号</p>
        </div>
        <div class="table-filters compact account-filters">
          <input v-model="search" type="search" placeholder="搜索账号" />
          <select v-model="role">
            <option value="">全部角色</option>
            <option value="admin">管理员</option>
            <option value="student">学生</option>
          </select>
        </div>
      </header>
      <div class="table-scroll">
        <table>
          <thead><tr><th>账号</th><th>角色</th><th></th></tr></thead>
          <tbody>
            <tr v-for="item in pagedAccounts" :key="item.account">
              <td class="strong-cell">{{ item.account }}</td>
              <td><span class="badge" :class="item.role === 'admin' ? 'ok' : 'warn'">{{ item.role }}</span></td>
              <td class="actions">
                <button type="button" @click="openEdit(item)">编辑</button>
                <button type="button" class="danger-button" @click="emit('deleteAccount', item)">删除</button>
              </td>
            </tr>
            <tr v-if="pagedAccounts.length === 0"><td class="empty-state" colspan="3">没有符合条件的账号</td></tr>
          </tbody>
        </table>
      </div>
      <PaginationBar
        :page="page"
        :page-count="pageCount"
        :page-size="pageSize"
        :total="filteredAccounts.length"
        @change-page="page = $event"
        @change-page-size="pageSize = $event"
      />
    </section>

    <section v-else-if="activeView === 'logs'" class="panel table-panel data-panel">
      <header class="panel-heading">
        <div>
          <h2>关键操作日志</h2>
          <p>最近 {{ auditLogs.length }} 条</p>
        </div>
      </header>
      <div class="table-scroll">
        <table>
          <thead><tr><th>时间</th><th>操作人</th><th>操作类型</th><th>详情</th></tr></thead>
          <tbody>
            <tr v-for="log in auditLogs" :key="log.log_id">
              <td>{{ log.created_at }}</td>
              <td>{{ log.operator_id || '-' }}</td>
              <td class="strong-cell">{{ log.action_type }}</td>
              <td>{{ log.detail || log.target_id }}</td>
            </tr>
            <tr v-if="auditLogs.length === 0"><td class="empty-state" colspan="4">暂无操作日志</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-else class="content-grid two action-workspace">
      <form class="panel form-grid" @submit.prevent="emit('createAccount')">
        <h2>新增账号</h2>
        <input v-model="accountForm.account" placeholder="账号" required />
        <input v-model="accountForm.password" placeholder="初始密码" required />
        <select v-model="accountForm.role">
          <option value="admin">管理员</option>
          <option value="student">学生</option>
        </select>
        <button class="primary" type="submit">创建账号</button>
      </form>

      <form class="panel form-grid" @submit.prevent="emit('updateAccount')">
        <h2>修改账号</h2>
        <input v-model="accountEditForm.account" placeholder="账号" required />
        <input v-model="accountEditForm.password" placeholder="新密码，留空则不修改" />
        <select v-model="accountEditForm.role">
          <option value="">角色不变</option>
          <option value="admin">管理员</option>
          <option value="student">学生</option>
        </select>
        <button class="primary" type="submit">保存修改</button>
      </form>
    </div>
  </section>
</template>

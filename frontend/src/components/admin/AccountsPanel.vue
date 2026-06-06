<!--
  学生宿舍管理系统 - 账号与权限管理面板
  包含账号增删改、角色配置和关键操作日志。
-->
<script setup lang="ts">
import type { Account, AccountEditForm, AccountForm, AuditLog } from '../../types'

defineProps<{
  accountEditForm: AccountEditForm
  accountForm: AccountForm
  accounts: Account[]
  auditLogs: AuditLog[]
}>()

defineEmits<{
  createAccount: []
  deleteAccount: [account: Account]
  fillAccountEdit: [account: Account]
  updateAccount: []
}>()
</script>

<template>
  <section class="stack">
    <div class="content-grid two">
      <form class="panel form-grid" @submit.prevent="$emit('createAccount')">
        <h2>新增账号</h2>
        <input v-model="accountForm.account" placeholder="账号" required />
        <input v-model="accountForm.password" placeholder="初始密码" required />
        <select v-model="accountForm.role">
          <option value="admin">管理员</option>
          <option value="student">学生</option>
        </select>
        <button class="primary" type="submit">创建账号</button>
      </form>

      <form class="panel form-grid" @submit.prevent="$emit('updateAccount')">
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

    <section class="panel table-panel">
      <h2>账号列表</h2>
      <table>
        <thead>
          <tr>
            <th>账号</th>
            <th>角色</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in accounts" :key="item.account">
            <td>{{ item.account }}</td>
            <td><span class="badge" :class="item.role === 'admin' ? 'ok' : 'warn'">{{ item.role }}</span></td>
            <td class="actions">
              <button type="button" @click="$emit('fillAccountEdit', item)">编辑</button>
              <button type="button" @click="$emit('deleteAccount', item)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel table-panel">
      <h2>关键操作日志</h2>
      <table>
        <tbody>
          <tr v-for="log in auditLogs" :key="log.log_id">
            <td>{{ log.created_at }}</td>
            <td>{{ log.operator_id || '-' }}</td>
            <td>{{ log.action_type }}</td>
            <td>{{ log.detail || log.target_id }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

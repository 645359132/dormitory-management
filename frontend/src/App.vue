<!--
  学生宿舍管理系统 - 根组件
  负责：
  - 未登录时显示登录界面
  - 登录后显示侧边栏 + 工作区布局
  - 管理员展示 6 个功能标签页，学生展示个人首页
-->
<script setup lang="ts">
import { adminTabs } from './constants'
import AccountsPanel from './components/admin/AccountsPanel.vue'
import AccessPanel from './components/admin/AccessPanel.vue'
import AdminOverview from './components/admin/AdminOverview.vue'
import BillsPanel from './components/admin/BillsPanel.vue'
import LoginView from './components/LoginView.vue'
import MaintenancePanel from './components/admin/MaintenancePanel.vue'
import ResidencePanel from './components/admin/ResidencePanel.vue'
import StudentDashboard from './components/student/StudentDashboard.vue'
import { useDormitoryApp } from './composables/useDormitoryApp'

// 从全局组合式函数中解构所有状态和方法
const {
  accountEditForm,
  accountForm,
  accounts,
  activeTab,
  auditLogs,
  auth,
  bills,
  billEditForm,
  billFilters,
  billForm,
  dormitories,
  error,
  hygiene,
  hygieneForm,
  itemForm,
  items,
  loading,
  loginForm,
  notice,
  occupancyRate,
  overview,
  repairEditForm,
  repairForm,
  repairs,
  resetForm,
  roomEditForm,
  roomForm,
  assignForm,
  statistics,
  statisticsFilters,
  students,
  studentForm,
  studentHome,
  studentUnpaidCount,
  visitorForm,
  visitors,
  assignStudent,
  createAccount,
  createBill,
  createHygiene,
  createItem,
  createRepair,
  createRoom,
  createStudent,
  createVisitor,
  deleteAccount,
  deleteBill,
  deleteRoom,
  deleteStudent,
  fillAccountEdit,
  fillRoomEdit,
  handleLogin,
  importStudents,
  leaveVisitor,
  logout,
  money,
  payBill,
  refresh,
  refreshBills,
  refreshStatistics,
  resetPassword,
  returnItem,
  statusClass,
  updateBill,
  updateRepair,
  updateAccount,
  updateRoom,
} = useDormitoryApp()
</script>

<template>
  <!-- 未登录：显示登录页 -->
  <LoginView
    v-if="!auth.token"
    :error="error"
    :loading="loading"
    :login-form="loginForm"
    @login="handleLogin"
  />

  <!-- 已登录：侧边栏 + 工作区布局 -->
  <div v-else class="app-shell">
    <!-- 左侧导航栏 -->
    <aside class="sidebar">
      <div class="brand">
        <span>DM</span>
        <div>
          <strong>宿舍管理</strong>
          <small>{{ auth.role === 'admin' ? '管理员端' : '学生端' }}</small>
        </div>
      </div>

      <!-- 管理员导航标签 -->
      <nav v-if="auth.role === 'admin'">
        <button
          v-for="tab in adminTabs"
          :key="tab.id"
          :class="{ active: activeTab === tab.id }"
          type="button"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </nav>

      <!-- 底部账号信息与退出 -->
      <div class="account">
        <span>{{ auth.account }}</span>
        <button type="button" @click="logout">退出</button>
      </div>
    </aside>

    <!-- 右侧工作区 -->
    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ auth.role === 'admin' ? 'Office Console' : 'Student Console' }}</p>
          <h1>{{ auth.role === 'admin' ? adminTabs.find((tab) => tab.id === activeTab)?.label : '我的宿舍' }}</h1>
        </div>
        <button type="button" class="ghost" :disabled="loading" @click="refresh">刷新</button>
      </header>

      <!-- 提示信息 -->
      <p v-if="error" class="message error">{{ error }}</p>
      <p v-if="notice" class="message ok">{{ notice }}</p>

      <!-- 管理员端：按标签页切换面板 -->
      <AdminOverview
        v-if="auth.role === 'admin' && activeTab === 'overview'"
        :filters="statisticsFilters"
        :money="money"
        :occupancy-rate="occupancyRate"
        :overview="overview"
        :statistics="statistics"
        @refresh-stats="refreshStatistics"
      />

      <ResidencePanel
        v-if="auth.role === 'admin' && activeTab === 'residence'"
        :assign-form="assignForm"
        :dormitories="dormitories"
        :reset-form="resetForm"
        :room-edit-form="roomEditForm"
        :room-form="roomForm"
        :student-form="studentForm"
        :students="students"
        @assign-student="assignStudent"
        @create-room="createRoom"
        @create-student="createStudent"
        @delete-room="deleteRoom"
        @delete-student="deleteStudent"
        @fill-room-edit="fillRoomEdit"
        @import-students="importStudents"
        @reset-password="resetPassword"
        @update-room="updateRoom"
      />

      <BillsPanel
        v-if="auth.role === 'admin' && activeTab === 'bills'"
        :bill-edit-form="billEditForm"
        :bill-filters="billFilters"
        :bill-form="billForm"
        :bills="bills"
        :money="money"
        :status-class="statusClass"
        @create-bill="createBill"
        @delete-bill="deleteBill"
        @pay-bill="payBill"
        @refresh-bills="refreshBills"
        @update-bill="updateBill"
      />

      <MaintenancePanel
        v-if="auth.role === 'admin' && activeTab === 'maintenance'"
        :hygiene="hygiene"
        :hygiene-form="hygieneForm"
        :money="money"
        :repair-edit-form="repairEditForm"
        :repairs="repairs"
        :status-class="statusClass"
        @create-hygiene="createHygiene"
        @update-repair="updateRepair"
      />

      <AccessPanel
        v-if="auth.role === 'admin' && activeTab === 'access'"
        :item-form="itemForm"
        :items="items"
        :status-class="statusClass"
        :visitor-form="visitorForm"
        :visitors="visitors"
        @create-item="createItem"
        @create-visitor="createVisitor"
        @leave-visitor="leaveVisitor"
        @return-item="returnItem"
      />

      <AccountsPanel
        v-if="auth.role === 'admin' && activeTab === 'accounts'"
        :account-edit-form="accountEditForm"
        :account-form="accountForm"
        :accounts="accounts"
        :audit-logs="auditLogs"
        @create-account="createAccount"
        @delete-account="deleteAccount"
        @fill-account-edit="fillAccountEdit"
        @update-account="updateAccount"
      />

      <!-- 学生端：个人首页 -->
      <StudentDashboard
        v-if="auth.role === 'student'"
        :money="money"
        :repair-form="repairForm"
        :status-class="statusClass"
        :student-home="studentHome"
        :unpaid-count="studentUnpaidCount"
        @create-repair="createRepair"
        @pay-bill="payBill"
      />
    </main>
  </div>
</template>

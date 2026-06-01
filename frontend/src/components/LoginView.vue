<!--
  学生宿舍管理系统 - 登录页面组件
  包含宣传信息和登录表单。
-->
<script setup lang="ts">
import heroImage from "../assets/hero.png";
import type { LoginForm } from "../types";

defineProps<{
  error: string; // 登录错误消息
  loading: boolean; // 登录加载状态
  loginForm: LoginForm; // 登录表单双向绑定对象
}>();

defineEmits<{
  login: []; // 提交登录事件
}>();
</script>

<template>
  <main class="login-page">
    <!-- 左侧：宣传图与系统介绍 -->
    <section class="login-visual">
      <img :src="heroImage" alt="" />
      <div>
        <p class="eyebrow">Dormitory Management</p>
        <h1>学生宿舍管理系统</h1>
        <p>住宿、账单、维修、卫生和出入登记集中处理。</p>
      </div>
    </section>

    <!-- 右侧：登录表单 -->
    <form class="login-form" @submit.prevent="$emit('login')">
      <h2>登录</h2>
      <label>
        账号
        <input v-model="loginForm.account" autocomplete="username" />
      </label>
      <label>
        密码
        <input
          v-model="loginForm.password"
          type="password"
          autocomplete="current-password"
        />
      </label>
      <button class="primary" type="submit" :disabled="loading">
        登录系统
      </button>
      <!-- 默认测试账号提示 -->
      <p class="hint">管理员 admin01 / admin123，学生 24050710 / 24050710</p>
      <p v-if="error" class="message error">{{ error }}</p>
    </form>
  </main>
</template>

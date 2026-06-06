<!--
  学生宿舍管理系统 - 出入登记管理面板
  包含：物品登记表单、访客登记表单、物品记录列表和访客记录列表。
-->
<script setup lang="ts">
import type { ItemForm, ItemRecord, VisitorForm, VisitorRecord } from '../../types'

defineProps<{
  itemForm: ItemForm                                // 物品登记表单
  items: ItemRecord[]                               // 物品记录列表
  statusClass: (value: string) => string            // 状态 CSS 类名函数
  visitorForm: VisitorForm                          // 访客登记表单
  visitors: VisitorRecord[]                         // 访客记录列表
}>()

defineEmits<{
  createItem: []                          // 登记物品
  createVisitor: []                       // 登记访客
  leaveVisitor: [visitor: VisitorRecord]  // 访客离开
  returnItem: [item: ItemRecord]          // 物品归还
}>()
</script>

<template>
  <section class="stack">
    <!-- 第一行：物品登记 + 访客登记 -->
    <div class="content-grid two">
      <form class="panel form-grid" @submit.prevent="$emit('createItem')">
        <h2>物品登记</h2>
        <input v-model="itemForm.student_id" placeholder="学号" required />
        <input v-model="itemForm.item_name" placeholder="物品名称" required />
        <select v-model="itemForm.action">
          <option>存入</option>
          <option>取出</option>
        </select>
        <input v-model.number="itemForm.quantity" type="number" min="1" placeholder="数量" />
        <input v-model="itemForm.remark" placeholder="备注" />
        <button class="primary" type="submit">登记物品</button>
      </form>

      <form class="panel form-grid" @submit.prevent="$emit('createVisitor')">
        <h2>访客登记</h2>
        <input v-model="visitorForm.visitor_name" placeholder="访客姓名" required />
        <input v-model="visitorForm.phone" placeholder="联系电话" />
        <input v-model="visitorForm.visit_student_id" placeholder="被访学生学号" required />
        <input v-model="visitorForm.remark" placeholder="备注" />
        <button class="primary" type="submit">登记访客</button>
      </form>
    </div>

    <!-- 第二行：物品记录 + 访客记录 -->
    <div class="content-grid two">
      <section class="panel table-panel">
        <h2>物品记录</h2>
        <table>
          <tbody>
            <tr v-for="item in items" :key="item.item_id">
              <td>{{ item.student_name || item.student_id }}</td>
              <td>{{ item.item_name }} x{{ item.quantity }}</td>
              <td><span class="badge" :class="statusClass(item.status)">{{ item.status }}</span></td>
              <td><button v-if="item.status !== '已归还'" type="button" @click="$emit('returnItem', item)">归还</button></td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel table-panel">
        <h2>访客记录</h2>
        <table>
          <tbody>
            <tr v-for="visitor in visitors" :key="visitor.visitor_id">
              <td>{{ visitor.visitor_name }}</td>
              <td>{{ visitor.building_no }} {{ visitor.room_no }}</td>
              <td><span class="badge" :class="statusClass(visitor.status)">{{ visitor.status }}</span></td>
              <td>
                <button v-if="visitor.status === '在访'" type="button" @click="$emit('leaveVisitor', visitor)">离开</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

  </section>
</template>

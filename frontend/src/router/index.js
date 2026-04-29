import { createRouter, createWebHashHistory } from 'vue-router'

import Home from '@/views/Home.vue'
import Dashboard from '@/views/Dashboard.vue'
import RepairCheck from '@/views/RepairCheck.vue'
import ExtendUsage from '@/views/ExtendUsage.vue'
import AIChat from '@/views/AIChat.vue'
import SafeGuidance from '@/views/SafeGuidance.vue'
import DisposalLocations from '@/views/DisposalLocations.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/repair-check',
    name: 'RepairCheck',
    component: RepairCheck,
  },
  {
    path: '/extend-usage',
    name: 'ExtendUsage',
    component: ExtendUsage,
  },
  {
    path: '/device-optimizer',
    name: 'DeviceOptimizer',
    component: AIChat,
  },
  {
    path: '/ai-chat',
    redirect: '/device-optimizer',
  },
  {
    path: '/safe-guidance',
    name: 'SafeGuidance',
    component: SafeGuidance,
  },
  {
    path: '/disposal-locations',
    name: 'DisposalLocations',
    component: DisposalLocations,
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router

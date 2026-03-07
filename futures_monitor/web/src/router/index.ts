/**
 * role: Define application routes for dashboard pages.
 * depends:
 *   - vue-router
 *   - ../views/DashboardView.vue
 * exports:
 *   - router
 * status: IMPLEMENTED
 * functions:
 *   - createRouterInstance() -> Router
 */

import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    }
  ]
})

export default router

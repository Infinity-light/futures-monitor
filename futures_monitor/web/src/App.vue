<!--
role: Root application shell composing router view and shared status bar.
depends:
  - vue
  - vue-router
  - ./components/StatusBar.vue
exports:
  - App
status: IMPLEMENTED
functions:
  - renderRootLayout() -> VNode
-->
<template>
  <div class="app-root">
    <StatusBar />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import StatusBar from './components/StatusBar.vue'
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f7fa;
  color: #303133;
}

#app {
  min-height: 100vh;
}

.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>

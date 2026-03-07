/**
 * role: Configure Vite build/dev server for Vue frontend.
 * depends:
 *   - vite
 *   - @vitejs/plugin-vue
 * exports:
 *   - default defineConfig
 * status: IMPLEMENTED
 * functions:
 *   - createViteConfig() -> UserConfig
 */

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  }
})

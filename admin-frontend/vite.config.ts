import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0'  // 允许外网访问
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})

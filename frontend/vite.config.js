import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/search': 'http://api:8000',
      '/dates':  'http://api:8000',
    },
  },
})

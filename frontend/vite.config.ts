import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const isProd = process.env.NODE_ENV === 'production'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  // En dev : base '/' → app à localhost:5173/ (routes normales)
  // En prod : base '/static/frontend/' → assets référencés comme /static/frontend/assets/...
  base: isProd ? '/static/frontend/' : '/',
  build: {
    outDir: '../static/frontend',
    emptyOutDir: true,
  },
})

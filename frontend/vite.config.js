import { defineConfig } from 'vite'

export default defineConfig({
  root: '.',
  publicDir: 'models',
  server: {
    port: 3000,
    open: '/startup.html',
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        main: './startup.html',
        login: './login.html',
        index: './index.html'
      }
    }
  }
})

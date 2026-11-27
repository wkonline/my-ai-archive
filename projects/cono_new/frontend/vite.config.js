import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    /* 局域网内有大量旧版 iOS/iPadOS 设备（iOS 15 及更早）。
       Vite 8 默认 target 是 baseline-widely-available，会把
       `@media (max-width: 900px)` 重写成 Level 4 范围语法
       `@media (width<=900px)`，而该语法需 Safari 16.4+。
       老 Safari 会整块忽略媒体查询 —— 表现为「电脑正常、手机没适配」。
       显式声明目标浏览器可让构建保留传统语法。 */
    target: ['es2015', 'safari14', 'chrome87', 'firefox78', 'edge88'],
    cssTarget: ['safari14', 'chrome87', 'firefox78', 'edge88'],
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})

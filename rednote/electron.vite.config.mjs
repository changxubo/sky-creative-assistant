import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@mcpserver': resolve('src-mcpserver/dist')
      }
    },
    build: {
      rollupOptions: {
        output: {
        charset: false // This can help with encoding issues
      },
        external: ['../../src-mcpserver/dist/index.js', '../../src-mcpserver/dist/xhs-browser.js']
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()]
  },
  renderer: {
    resolve: {
      alias: {
        '@renderer': resolve('src/renderer/src')
      }
    },
    plugins: [react()]
  }
})

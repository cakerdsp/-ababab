// electron.vite.config.js
import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'

// 自定义插件：复制class目录到构建输出
function copyClassPlugin() {
  return {
    name: 'copy-class',
    writeBundle() {
      // 复制class目录到out目录
      const srcPath = resolve(process.cwd(), 'src/class')
      const destPath = resolve(process.cwd(), 'out/class')

      if (fs.existsSync(srcPath)) {
        // 递归复制目录
        function copyDir(src, dest) {
          if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true })
          }
          const entries = fs.readdirSync(src, { withFileTypes: true })
          for (let entry of entries) {
            const srcPath = resolve(src, entry.name)
            const destPath = resolve(dest, entry.name)
            if (entry.isDirectory()) {
              copyDir(srcPath, destPath)
            } else {
              fs.copyFileSync(srcPath, destPath)
            }
          }
        }
        copyDir(srcPath, destPath)
        console.log('Class directory copied to out/class')
      }
    }
  }
}

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin(), copyClassPlugin()],
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/main/index.js')
        },
        external: ['electron', 'path', 'url', 'fs', 'child_process']
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()]
  },
  renderer: {
    resolve: {
      alias: {
        '@': resolve('src/renderer/src')
      }
    },
    plugins: [vue()],
    build: {
      rollupOptions: {
        external: [],
        output: {
          globals: {}
        }
      },
      commonjsOptions: {
        include: [/lodash/, /node_modules/]
      }
    },
    optimizeDeps: {
      include: ['lodash-es', 'lodash-unified']
    },
    server: {
      hmr: true,
      port: 9000,
      proxy: {
        "/api": {
          target: "http://localhost:9000",
          changeOrigin: true,
          pathRewrite: {
            "^api": "/api"
          }
        }
      }
    }
  }
})

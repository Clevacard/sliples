import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Load SSL certs if available (for local HTTPS with sliples.localhost.in)
const httpsConfig = (() => {
  const certPath = path.resolve(__dirname, 'certs/sliples.localhost.in.pem')
  const keyPath = path.resolve(__dirname, 'certs/sliples.localhost.in-key.pem')
  if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
    return {
      key: fs.readFileSync(keyPath),
      cert: fs.readFileSync(certPath),
    }
  }
  return undefined
})()

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    https: httpsConfig,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/openapi.json': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/redoc': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})

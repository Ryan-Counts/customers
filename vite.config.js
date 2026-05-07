import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/backend': 'http://localhost:5000',
      '/customers': 'http://localhost:5000',
      '/imports': 'http://localhost:5000'
    },
  },
})

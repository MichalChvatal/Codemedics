import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build', // Specify the output directory here
    emptyOutDir: true, // Ensures that the output directory is emptied before each build (optional, but recommended)
  },
})

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // For `npm run dev`: forward /api/* to a Spring Boot running on localhost:8080.
    // In Docker, nginx handles this proxy instead.
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true }
    }
  }
});

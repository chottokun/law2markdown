import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  base: process.env.VITE_BASE_PATH ?? '/law2markdown/',
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
  },
  optimizeDeps: {
    exclude: ['@duckdb/duckdb-wasm'],
  },
  build: {
    target: 'es2022',
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});

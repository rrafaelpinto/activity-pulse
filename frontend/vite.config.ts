import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The Django API runs on 8000; proxying keeps the page and the API on one origin (no CORS).
const api = { "/api": "http://127.0.0.1:8000" };

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: api },
  preview: { port: 4173, proxy: api },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
  },
});

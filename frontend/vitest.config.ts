import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "node",
    include: ["tests/**/*.test.{ts,tsx}"],
    pool: "forks",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
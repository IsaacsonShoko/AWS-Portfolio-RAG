import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  test: { environment: "jsdom", setupFiles: ["./test/setup.ts"], globals: true },
  build: {
    lib: {
      entry: "src/embed.tsx",
      name: "FourDAssistant",
      fileName: "fourd-assistant",
      formats: ["es", "umd"],
    },
  },
});

import { defineConfig } from "vite";

export default defineConfig({
  root: "frontend",
  envDir: "frontend",
  base: "/",
  build: { outDir: "../dist", emptyOutDir: true },
  server: { host: "0.0.0.0", port: 3000 }
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { viteStaticCopy } from "vite-plugin-static-copy";

export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        {
          src: "node_modules/cesium/Build/Cesium/Workers",
          dest: "cesium",
        },
        {
          src: "node_modules/cesium/Build/Cesium/ThirdParty",
          dest: "cesium",
        },
        {
          src: "node_modules/cesium/Build/Cesium/Assets",
          dest: "cesium",
        },
        {
          src: "node_modules/cesium/Build/Cesium/Widgets",
          dest: "cesium",
        },
      ],
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    CESIUM_BASE_URL: JSON.stringify("/cesium"),
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 5000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (["react","react-dom","react-router-dom"].some((p) => id.includes(p))) return "vendor";
            if (id.includes("recharts")) return "charts";
            if (id.includes("zustand") || id.includes("tanstack")) return "state";
          }
        },
      },
    },
  },
});

// filepath: c:\Users\kalya\Desktop\AI Projects\document-gen\vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: "../postcss.config.js",
  },
});

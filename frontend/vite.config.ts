import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// Configuração do Vite (nada de compilerOptions aqui)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  }
});

import { defineConfig } from 'vite'

// `npm run dev` abre directo en el quinto postulado, que es el episodio de la charla.
// VITE_NO_OPEN=1 evita abrir el navegador (para lanzarlo desde otra herramienta).
export default defineConfig({
  server: { open: process.env.VITE_NO_OPEN ? false : '/?ep=quinto' },
  build: { target: 'es2022' },
})

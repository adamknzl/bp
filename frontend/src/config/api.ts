export const API_BASE_URL =
  (import.meta as ImportMeta & { env: Record<string, string> }).env?.VITE_API_URL ??
  'http://localhost:3000/api';
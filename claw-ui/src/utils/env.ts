export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE || 'http://localhost:8000'
}

export function isDevelopment(): boolean {
  return import.meta.env.DEV === true
}

export function isProduction(): boolean {
  return import.meta.env.PROD === true
}
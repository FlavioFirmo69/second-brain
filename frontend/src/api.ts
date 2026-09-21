const base = import.meta.env.VITE_API_URL || ''

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${base}/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  })
  if (!response.ok) {
    let detail = response.statusText
    try { detail = (await response.json()).detail || detail } catch { /* ignore */ }
    throw new Error(detail)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const post = <T>(path: string, body?: unknown) => api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
export const put = <T>(path: string, body: unknown) => api<T>(path, { method: 'PUT', body: JSON.stringify(body) })
export const remove = (path: string) => api<void>(path, { method: 'DELETE' })

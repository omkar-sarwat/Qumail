

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

const DEV_SESSION_TOKEN = import.meta.env.VITE_DEV_SESSION_TOKEN || 'VALID_ACCESS_TOKEN'
const STORAGE_KEY = 'qumail_session_token'

const jsonHeaders = new Headers({ 'Content-Type': 'application/json' })

function resolveToken(): string | null {
  return localStorage.getItem(STORAGE_KEY) || DEV_SESSION_TOKEN
}

function buildUrl(path: string, query?: Record<string, string | number | boolean | undefined | null>): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  if (!query) {
    return `${API_BASE_URL}${normalizedPath}`
  }
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    params.append(key, String(value))
  })
  const qs = params.toString()
  return qs ? `${API_BASE_URL}${normalizedPath}?${qs}` : `${API_BASE_URL}${normalizedPath}`
}

async function request<T>(
  path: string,
  options: RequestInit & { query?: Record<string, string | number | boolean | undefined | null> } = {}
): Promise<T> {
  const { query, headers, body, method = 'GET', ...rest } = options
  const url = buildUrl(path, query)
  const token = resolveToken()

  const finalHeaders = new Headers(headers)
  if (!(body instanceof FormData)) {
    jsonHeaders.forEach((value, key) => {
      if (!finalHeaders.has(key)) {
        finalHeaders.set(key, value)
      }
    })
  }
  if (token && !finalHeaders.has('Authorization')) {
    finalHeaders.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(url, {
    method,
    body,
    headers: finalHeaders,
    credentials: 'include',
    ...rest
  })

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText)
    throw new Error(text || `Request failed with status ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export async function fetchCurrentUser() {
  return request('/api/v1/auth/me')
}

export async function fetchEmails(folder: string, params?: { pageToken?: string; maxResults?: number }) {
  return request(`/api/v1/emails/${folder}`, {
    query: {
      page_token: params?.pageToken,
      max_results: params?.maxResults
    }
  })
}

export async function fetchEmailDetail(emailId: string) {
  return request(`/api/v1/emails/email/${emailId}`)
}

export async function decryptEmail(emailId: string) {
  return request(`/api/v1/emails/email/${emailId}/decrypt`, { method: 'POST' })
}

export async function sendEmail(formData: FormData) {
  return request('/api/v1/emails/send', {
    method: 'POST',
    body: formData,
    headers: new Headers() // Allow browser to set multipart boundaries
  })
}

export async function syncGmail() {
  return request('/api/v1/emails/sync/gmail', { method: 'POST' })
}

export function persistToken(token: string) {
  localStorage.setItem(STORAGE_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(STORAGE_KEY)
}

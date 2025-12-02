const STYLE_TAG = /<style[\s\S]*?<\/style>/gi
const SCRIPT_TAG = /<script[\s\S]*?<\/script>/gi
const LINK_STYLESHEET = /<link[^>]+rel=['"]?stylesheet['"]?[^>]*>/gi
const META_TAG = /<meta[^>]*>/gi
const HEAD_TAG = /<head[\s\S]*?<\/head>/gi
const HTML_TAG = /<\/?html[^>]*>/gi
const BODY_OPEN_TAG = /<body([^>]*)>/gi
const BODY_CLOSE_TAG = /<\/body>/gi

const PLACEHOLDER = '<p class="text-gray-400 italic">No content available</p>'

const isLikelyHtml = (value: string) => /<[a-z][\s\S]*>/i.test(value)

const escapeHtml = (value: string) =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

export const sanitizeEmailHtml = (raw: string): string => {
  if (!raw) return ''
  let sanitized = raw
    .replace(STYLE_TAG, '')
    .replace(SCRIPT_TAG, '')
    .replace(LINK_STYLESHEET, '')
    .replace(META_TAG, '')
    .replace(HEAD_TAG, '')
    .replace(HTML_TAG, '')

  sanitized = sanitized.replace(BODY_OPEN_TAG, '<div data-email-body$1>')
  sanitized = sanitized.replace(BODY_CLOSE_TAG, '</div>')

  return sanitized
}

export const normalizeEmailBody = (raw?: string | null, fallback = PLACEHOLDER): string => {
  if (!raw) return fallback
  const trimmed = raw.trim()
  if (!trimmed) return fallback

  if (!isLikelyHtml(trimmed)) {
    const escaped = escapeHtml(trimmed)
    const html = escaped
      .split(/\n\n+/)
      .map((paragraph) => `<p>${paragraph.replace(/\n/g, '<br/>')}</p>`)
      .join('')
    return html || fallback
  }

  const sanitized = sanitizeEmailHtml(trimmed)
  return sanitized || fallback
}

export const EMAIL_PLACEHOLDER_HTML = PLACEHOLDER

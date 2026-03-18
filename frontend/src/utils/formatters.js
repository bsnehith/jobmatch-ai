export function toTitleCase(value = '') {
  return String(value)
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((word) => `${word[0]?.toUpperCase() || ''}${word.slice(1).toLowerCase()}`)
    .join(' ')
}

export function normalizeList(input) {
  if (Array.isArray(input)) return input
  if (typeof input === 'string') {
    return input
      .split(/[,\n]+/)
      .map((item) => item.trim())
      .filter(Boolean)
  }
  return []
}

export function formatDate(dateText) {
  if (!dateText) return '-'
  // Handle legacy SQLite timestamps ("YYYY-MM-DD HH:MM:SS") as UTC.
  const normalized =
    typeof dateText === 'string' && dateText.includes(' ') && !dateText.endsWith('Z')
      ? `${dateText.replace(' ', 'T')}Z`
      : dateText
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return String(dateText)
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  }).format(date)
}

export function getCandidateRows(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.data)) return payload.data
  if (Array.isArray(payload?.candidates)) return payload.candidates
  if (payload?.candidate) return [payload.candidate]
  return []
}

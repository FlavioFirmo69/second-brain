export function isoDateLocal(value = new Date()) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function formatDate(value?: string | null) {
  if (!value) return '—'
  const [year, month, day] = value.slice(0, 10).split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

export function formatDateTime(value?: string | null) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))
}

export function addDays(value: Date, days: number) {
  const copy = new Date(value)
  copy.setDate(copy.getDate() + days)
  return copy
}

export function startOfWeek(value: Date) {
  const copy = new Date(value)
  const day = (copy.getDay() + 6) % 7
  copy.setDate(copy.getDate() - day)
  copy.setHours(12, 0, 0, 0)
  return copy
}

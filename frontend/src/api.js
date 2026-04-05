export async function getDates() {
  const res = await fetch('/dates')
  if (!res.ok) return {}
  return res.json()
}

export async function search(question, ticker) {
  const res = await fetch('/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, ticker: ticker || null }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

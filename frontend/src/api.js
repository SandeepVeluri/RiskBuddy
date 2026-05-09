export async function getFunds() {
  const r = await fetch('/api/funds')
  if (!r.ok) throw new Error(`Failed to load funds (${r.status})`)
  return r.json()
}

export async function simulateFund(schemeCode) {
  const r = await fetch(`/api/simulate/${schemeCode}`)
  if (!r.ok) {
    const text = await r.text()
    throw new Error(`Simulation failed (${r.status}): ${text}`)
  }
  return r.json()
}

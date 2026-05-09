import { useEffect, useState } from 'react'
import { getFunds, simulateFund } from './api'
import RiskChart from './RiskChart'

export default function App() {
  const [funds, setFunds] = useState([])
  const [selected, setSelected] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getFunds()
      .then((d) => {
        setFunds(d.funds)
        if (d.funds.length > 0) setSelected(d.funds[0].scheme_code)
      })
      .catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    setError('')
    setResult(null)
    simulateFund(selected)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [selected])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">RiskBuddy</h1>
          <p className="text-sm text-gray-600 mt-1">
            Phase 1 — Single fund risk chart. Each dot is one possible historical entry point.
          </p>
        </header>

        <div className="mb-6">
          <label htmlFor="fund" className="block text-sm font-medium text-gray-700 mb-1">
            Fund
          </label>
          <select
            id="fund"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="w-full sm:w-auto border border-gray-300 rounded px-3 py-2 bg-white"
          >
            {funds.map((f) => (
              <option key={f.scheme_code} value={f.scheme_code}>
                {f.name} ({(f.weight * 100).toFixed(0)}%)
              </option>
            ))}
          </select>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          {loading && <div className="text-gray-500 py-12 text-center">Loading NAV history…</div>}
          {error && (
            <div className="text-red-700 bg-red-50 border border-red-200 rounded p-3 text-sm">
              {error}
            </div>
          )}
          {result && !loading && (
            <RiskChart
              records={result.records}
              meanCagr={result.mean_cagr}
              fundName={result.fund.name}
            />
          )}
        </div>

        <footer className="mt-8 text-xs text-gray-500">
          This shows what was possible in the past. Markets can behave in ways history has never
          seen.
        </footer>
      </div>
    </div>
  )
}

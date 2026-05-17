import { useEffect, useState } from 'react'
import { getFunds, simulateFund, simulatePortfolio } from './api'
import RiskChart from './RiskChart'

const ORDER = ['1M', '3M', '6M', '1Y', '2Y', '3Y', '4Y', '5Y']
const PORTFOLIO_KEY = 'portfolio'

export default function App() {
  const [funds, setFunds] = useState([])
  const [selected, setSelected] = useState(PORTFOLIO_KEY)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedPeriod, setSelectedPeriod] = useState('3Y')

  useEffect(() => {
    getFunds()
      .then((d) => setFunds(d.funds))
      .catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    setError('')
    setResult(null)
    const p = selected === PORTFOLIO_KEY ? simulatePortfolio() : simulateFund(selected)
    p.then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [selected])

  const isPortfolio = selected === PORTFOLIO_KEY
  const periodIdx = ORDER.indexOf(selectedPeriod)
  const chartTitle = isPortfolio ? 'Blended Portfolio' : result?.fund?.name ?? ''

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">RiskBuddy</h1>
          <p className="text-sm text-gray-600 mt-1">
            Each dot is one possible historical entry point. Spread = risk.
          </p>
        </header>

        <div className="mb-6">
          <label htmlFor="view" className="block text-sm font-medium text-gray-700 mb-1">
            View
          </label>
          <select
            id="view"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="w-full sm:w-auto border border-gray-300 rounded px-3 py-2 bg-white"
          >
            <option value={PORTFOLIO_KEY}>Blended Portfolio (all funds)</option>
            {funds.map((f) => (
              <option key={f.scheme_code} value={f.scheme_code}>
                {f.name} ({(f.weight * 100).toFixed(0)}%)
              </option>
            ))}
          </select>
        </div>

        {isPortfolio && result && !loading && (
          <div className="mb-4">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">Holding period</span>
              <span className="text-sm font-semibold text-gray-900">{selectedPeriod}</span>
            </div>
            <input
              type="range"
              min="0"
              max="7"
              step="1"
              value={periodIdx === -1 ? 5 : periodIdx}
              onChange={(e) => setSelectedPeriod(ORDER[parseInt(e.target.value)])}
              className="w-full accent-[#97144d]"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              {ORDER.map((p) => (
                <span key={p} className={p === selectedPeriod ? 'font-semibold text-gray-700' : ''}>
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          {loading && (
            <div className="text-gray-500 py-12 text-center">Loading NAV history…</div>
          )}
          {error && (
            <div className="text-red-700 bg-red-50 border border-red-200 rounded p-3 text-sm">
              {error}
            </div>
          )}
          {result && !loading && (
            <RiskChart
              records={result.records}
              meanCagr={result.mean_cagr}
              fundName={chartTitle}
              selectedPeriod={isPortfolio ? selectedPeriod : null}
              insufficientFunds={result.insufficient_funds || {}}
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

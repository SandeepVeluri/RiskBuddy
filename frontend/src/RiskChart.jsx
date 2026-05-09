import Plot from 'react-plotly.js'

const ORDER = ['1M', '3M', '6M', '1Y', '2Y', '3Y', '4Y', '5Y']

export default function RiskChart({ records, meanCagr, fundName }) {
  if (!records || records.length === 0) {
    return <div className="text-gray-500">No simulation data.</div>
  }

  const x = records.map((r) => r.holding_period)
  const y = records.map((r) => r.cagr)
  const customdata = records.map((r) => [r.abs_return, r.start_date, r.end_date])

  const minCagr = Math.min(...y)
  const maxCagr = Math.max(...y)
  const yPadding = (maxCagr - minCagr) * 0.05 || 1
  const yMin = minCagr - yPadding
  const yMax = maxCagr + yPadding

  const negCount = y.filter((v) => v < 0).length
  const negPct = ((negCount / y.length) * 100).toFixed(1)

  const data = [
    {
      type: 'scatter',
      mode: 'markers',
      x,
      y,
      customdata,
      marker: {
        color: '#97144d',
        size: 7,
        opacity: 0.55,
      },
      hovertemplate:
        'CAGR: %{y:.2f}%<br>' +
        'Abs Return: %{customdata[0]:.2f}%<br>' +
        'Start: %{customdata[1]}<br>' +
        'End: %{customdata[2]}<extra></extra>',
      name: 'Entry points',
    },
  ]

  const shapes = [
    {
      type: 'rect',
      xref: 'paper',
      yref: 'y',
      x0: 0,
      x1: 1,
      y0: yMin,
      y1: 0,
      fillcolor: 'rgba(255, 0, 0, 0.12)',
      line: { width: 0 },
      layer: 'below',
    },
    {
      type: 'line',
      xref: 'paper',
      yref: 'y',
      x0: 0,
      x1: 1,
      y0: meanCagr,
      y1: meanCagr,
      line: { color: 'gray', width: 1, dash: 'dash' },
    },
  ]

  const annotations = [
    {
      xref: 'paper',
      yref: 'y',
      x: 0.01,
      y: meanCagr,
      xanchor: 'left',
      yanchor: 'bottom',
      text: `Mean CAGR: ${meanCagr.toFixed(2)}%`,
      showarrow: false,
      font: { color: 'gray', size: 11 },
    },
  ]

  const layout = {
    title: {
      text: fundName ? `${fundName} — Historical CAGR by holding period` : 'Historical CAGR',
      font: { size: 15 },
    },
    xaxis: {
      title: 'Holding period',
      type: 'category',
      categoryorder: 'array',
      categoryarray: ORDER,
    },
    yaxis: {
      title: 'CAGR (%)',
      range: [yMin, yMax],
      zeroline: true,
      zerolinecolor: '#999',
    },
    shapes,
    annotations,
    showlegend: false,
    margin: { l: 50, r: 20, t: 50, b: 50 },
    height: 480,
    template: 'plotly_white',
  }

  return (
    <div>
      <Plot
        data={data}
        layout={layout}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
        useResizeHandler
      />
      <p className="text-sm text-gray-600 mt-2">
        {records.length} historical entry points simulated. {negCount} ({negPct}%) ended in
        negative CAGR.
      </p>
    </div>
  )
}

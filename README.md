# RiskBuddy

Portfolio risk visualiser for Indian mutual fund investors. Stress-tests today's portfolio against every historical entry point.

## Status: Phase 1 — Mock Data + Single Fund Chart

Phase 1 scope (per `master_brief.md`):
- 3 hard-coded mock funds (Axis Small Cap, HDFC Corp Bond, ICICI Pru Balanced Advantage)
- Live NAV history fetched from MFapi.in
- Correct CAGR formula: `((nav_end / nav_start) ^ (1 / years) - 1) * 100`
- Single-fund Plotly dot plot with fund selector, mean line, negative-return red band
- FastAPI backend + React (Vite) + Tailwind frontend, served as one process in production

Out of scope until later phases: blended portfolio, holding-period slider, user entry highlight, cohort logic, mobile UI polish, CAS PDF parsing.

## Repo layout

```
backend/        FastAPI app
  main.py       routes + CORS + static mount of frontend/dist
  funds.py      mock portfolio (3 funds + weights)
  mfapi.py      MFapi.in fetcher with in-memory NAV cache
  simulation.py entry-date loop + CAGR formula
frontend/       Vite + React (JS) + Tailwind
  src/App.jsx       fund selector + chart wrapper
  src/RiskChart.jsx Plotly dot plot
  src/api.js        fetch wrapper
master_brief.md the spec
scheme interactive risk chart.py  original Dash prototype (reference)
```

## Run locally

### Backend

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

API: `http://localhost:8000/api/health`, `/api/funds`, `/api/simulate/{scheme_code}`.

### Frontend (dev)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api/*` to the backend on :8000.

### Production build (single-service deploy)

```bash
cd frontend && npm run build      # outputs frontend/dist/
cd .. && uvicorn backend.main:app --port 8000
```

Now `http://localhost:8000` serves the built React app *and* the API. This is the form to deploy to Railway / Render / similar.

## Phase 1 validation checklist

Before signing off Phase 1, confirm:
- [ ] Fund selector lists all 3 funds.
- [ ] Selecting Axis Small Cap renders the dot plot in <5s.
- [ ] Spread visibly narrows from 1M → 5Y.
- [ ] Mean CAGR dashed line is visible.
- [ ] Red band sits below y=0.
- [ ] Hover on a dot shows CAGR, abs return, start date, end date.
- [ ] HDFC Corporate Bond chart looks much flatter (low vol).
- [ ] Pick one dot from the chart — manually compute `((nav_end/nav_start)^(1/years) - 1) * 100` from raw NAVs and confirm it matches within 0.01%.

The simulation math has been validated in this repo against synthetic NAV data (12% CAGR clean trend → all holding periods converge to ~12% as expected, spread narrows from 1M to 5Y).

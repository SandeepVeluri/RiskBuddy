from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .funds import MOCK_PORTFOLIO, get_fund
from .mfapi import fetch_nav_history
from .simulation import ORDER, simulate_portfolio, simulate_single_fund

app = FastAPI(title="RiskBuddy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/funds")
def list_funds():
    return {"funds": MOCK_PORTFOLIO, "holding_periods": ORDER}


@app.get("/api/simulate/portfolio")
def simulate_portfolio_endpoint():
    try:
        funds_data = [
            {
                "df": fetch_nav_history(f["scheme_code"]),
                "code": f["scheme_code"],
                "weight": f["weight"],
            }
            for f in MOCK_PORTFOLIO
        ]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MFapi fetch failed: {e}")

    records, insufficient = simulate_portfolio(funds_data)
    mean_cagr = sum(r["cagr"] for r in records) / len(records) if records else 0.0
    return {
        "records": records,
        "mean_cagr": round(mean_cagr, 4),
        "holding_periods": ORDER,
        "insufficient_funds": insufficient,
        "portfolio": MOCK_PORTFOLIO,
    }


@app.get("/api/simulate/{scheme_code}")
def simulate(scheme_code: str):
    fund = get_fund(scheme_code)
    if fund is None:
        raise HTTPException(status_code=404, detail="Unknown scheme code")

    try:
        df = fetch_nav_history(scheme_code)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MFapi fetch failed: {e}")

    records = simulate_single_fund(df)
    mean_cagr = (
        sum(r["cagr"] for r in records) / len(records) if records else 0.0
    )
    return {
        "fund": fund,
        "records": records,
        "mean_cagr": round(mean_cagr, 4),
        "holding_periods": ORDER,
    }


_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")

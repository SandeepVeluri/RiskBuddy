# Portfolio Risk Visualiser — Master Brief for Claude Code

## Product Vision

A mobile-optimised website that helps average Indian investors understand the risk they currently hold in their mutual fund portfolio — through the lens of historical possibilities, not predictions.

The tool debunks mutual fund risk for three types of users:

- **Oshi** — 25 year old, just started investing, only understands returns, needs plain language
- **Mayank** — 30 year old, self-managed portfolio, wants deeper data-driven insights
- **Sarita** — 35 year old, researches funds independently, hits a wall with technical content

One interface serves all three through **progressive disclosure** — simple layer first, depth revealed only when user curiosity triggers it. No profile selector. No cognitive load on user.

-----

## Core Mental Model

> “If someone with your exact portfolio today had started investing at every possible point in history — here is the range of outcomes they could have seen.”

This is NOT historical simulation of what happened. It is stress testing today’s portfolio against history.

Every dot on the chart = one possible historical entry point into this portfolio.
The spread of dots = risk.
Red area below zero = % of entry points that resulted in negative returns = risk metric.

-----

## Input Pipeline

### What the user provides:

1. **Detailed CAS PDF** — downloaded from CAMS (https://www.camsonline.com) or KFintech (https://mfs.kfintech.com)
1. **PAN number** — to unlock PDF (password = first 4 letters of PAN uppercase + DOB in DDMMYYYY format)
1. **Date of Birth** — to unlock PDF

### What the tool derives automatically (zero manual entry):

- Fund names → mapped to MFapi scheme codes
- Transaction history → derive current units held per fund
- Current units × latest NAV → current market value per fund
- Current market values → portfolio weights (weight_i = market_value_i / total_portfolio_value)
- First transaction date per fund → user’s entry date into that fund
- Historical NAVs → fetched from MFapi for all funds

### Data source for NAVs:

- **MFapi.in** — free, no authentication required
- Base URL: https://api.mfapi.in
- Key endpoint: `GET /mf/{scheme_code}` — returns full NAV history
- Search endpoint: `GET /mf/search?q={fund_name}` — to map fund names to scheme codes
- Cache NAV data — do not fetch on every request, rate limiting applies
- NAV data returns in reverse chronological order (newest first)

-----

## Core Mathematics

### CAGR Formula (single fund):

```
CAGR = ((nav_end / nav_start) ^ (1 / years) - 1) * 100
```

Where `years = holding_period_months / 12`

**CRITICAL NOTE:** The existing code uses absolute return formula `((nav_end - nav_start) / nav_start) * 100` — this is INCORRECT for CAGR and must be replaced everywhere.

### Blended Portfolio CAGR (multiple funds):

```
Blended ratio = Σ (weight_i × nav_end_i / nav_start_i)
Portfolio CAGR = (Blended ratio ^ (1 / years) - 1) * 100
```

This correctly replicates what a user sees on Groww/Zerodha dashboard.

Weights are fixed at TODAY’s AUM proportions across all historical simulations.

### Risk Metric:

```
Risk at holding period X = (number of entry points with negative CAGR at X) / (total entry points at X) × 100
```

Expressed as: “X% of entry points resulted in negative returns”

### Entry Dates for Simulation:

- Use first trading day of each month across full NAV history
- This gives one dot per month per holding period

### Holding Periods:

```
["1M", "3M", "6M", "1Y", "2Y", "3Y", "4Y", "5Y"]
months = [1, 3, 6, 12, 24, 36, 48, 60]
```

For exit date: find first available NAV on or after (entry_date + holding_period_months).

-----

## Feature List

### Feature 1 — Input & Onboarding

- CAS PDF upload interface
- PAN + DOB input fields
- PDF unlock using pdfplumber with password
- Automatic parsing of fund names and transaction history
- Derive current units from transaction history (buys - redemptions)
- Fetch latest NAV from MFapi → compute current market value
- Derive portfolio weights

### Feature 2 — Opening Statement (10 second experience)

- Single bold contextual sentence shown immediately after parsing
- Format: *“You are currently in the [positive/negative] returns group. X% of entry points in [month/year of first transaction] resulted in negative returns at your current holding period of [N years].”*
- Cohort comparison at three levels of granularity — same year, same quarter, same month
- Show most precise cohort that has sufficient data points (minimum 3 entry points)
- This is Layer 1 — Oshi stops here

### Feature 3 — Individual Fund Risk Charts

- One chart per fund in portfolio
- Dot plot: x-axis = holding period (1M → 5Y), y-axis = CAGR %
- Each dot = one possible historical entry point (first trading day of each month)
- Dot color: default maroon (#97144d), user’s entry year highlighted in blue
- Red shaded area: covers all negative return region below zero x-axis
- Green shaded band: min to max range for user’s entry year
- User’s own entry point: highlighted with distinct marker + cohort context tooltip
- Cohort tooltip: *“Entry points in [month/year] had X% chance of negative returns at your current holding period”*
- Spread visually narrows at longer holding periods — this is the key risk reduction story
- Mean CAGR line shown as dashed horizontal line
- Collapsible section below chart: *“Why does this fund behave this way?”* — 2-3 lines plain language, no jargon
- This is Layer 2 — Mayank engages here

### Feature 4 — Blended Portfolio Risk Chart

- All funds blended using the correct formula above
- Weights fixed at current AUM proportions
- Same dot plot structure as individual fund charts
- Holding period slider — user can explore 1M to 5Y
- Funds with insufficient history at selected holding period: contribution greyed out with clear warning label
- Summary note in comparison framing: *“Your portfolio has historically been [riskier/safer] than a Nifty 50 index fund but rewarded patient investors [X]% of the time”*
- This is Layer 2

### Feature 5 — Risk Contribution Breakdown

- Ranked list of funds by their individual risk metric (% negative entry points at user’s current holding period)
- Most risky fund shown first
- Plain language per fund: *“Small Cap Fund drove the most risk in your portfolio. Consider monitoring this fund closely.”*
- This is Layer 3 — Sarita reads here

### Feature 6 — Progressive Disclosure

- Layer 1: Opening statement only — visible immediately, no scroll required
- Layer 2: Charts revealed on tap/scroll — *“See your risk chart”* CTA
- Layer 3: Fund explanation + risk breakdown — collapsible sections within charts
- No profile selector — depth triggered entirely by user curiosity and interaction

### Feature 7 — Honest Disclaimers

- Persistent footer: *“This shows what was possible in the past. Markets can behave in ways history has never seen.”*
- Greyed fund contributions clearly labelled with reason
- No predictions. No buy/sell recommendations. Historical possibilities only.
- PAN and DOB used only to unlock PDF — never stored, never transmitted beyond local session

-----

## Tech Stack

|Layer      |Technology               |Reason                                                               |
|-----------|-------------------------|---------------------------------------------------------------------|
|Frontend   |React + Tailwind CSS     |Mobile responsive, best ecosystem for interactive charts             |
|Charts     |Plotly.js (React wrapper)|Mirrors existing Python Plotly logic, interactive dot plots          |
|Backend    |Python FastAPI           |Existing simulation code is Python, fast and lightweight             |
|PDF Parsing|pdfplumber               |Handles password protected PDFs, best structured extraction          |
|NAV Data   |MFapi.in                 |Free, no auth, full historical NAV for all Indian MFs                |
|Hosting    |Railway                  |Free tier, supports React + Python in one project, GitHub integration|
|Database   |None                     |No user data stored, everything computed per session                 |

-----

## Existing Code Reference

The following is the full existing prototype code. Read it carefully before building anything.

**What to reuse:**

- Simulation loop structure (entry dates, holding periods, records list)
- Plotly dot plot structure (scatter, bands, hline)
- Holding period ordering logic

**What to replace:**

- Dash app → FastAPI + React
- Redshift DB connection → MFapi
- INCORRECT CAGR formula → correct formula (see Core Mathematics section)
- AbsReturn placeholder → keep as separate metric, compute correctly

```python
import pandas as pd
query =f"""

SELECT nav_value_in_inr as "nav" , nav_reporting_time as "date" FROM digital.daily_nav_dimension where scheme_code='SV' and plan_code = 'DG';

"""

#Connect to the cluster
import redshift_connector
conn = redshift_connector.connect(
     host='axis-mf-dwh-prod-redshift-cluster-new.cwudrrkve8hj.ap-south-1.redshift.amazonaws.com',
     database='dwh-prod',
     port=5435,
     user='digital_usr',
     password='B3721531938y$'
)
             
cursor = conn.cursor()

cursor.execute(query)

df = pd.DataFrame(cursor.fetchall(), columns = [desc[0] for desc in cursor.description])

# Ensure nav is numeric
df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
df["date"] = pd.to_datetime(df["date"])
df = df.set_index("date").sort_index()



##########################################
# First trading day of each month
first_trades = df.groupby(df.index.to_period("M")).apply(lambda grp: grp.index.min())
entry_dates = first_trades.tolist()

holding_periods = {
    "1M":  1,
    "3M":  3,
    "6M":  6,
    "1Y": 12,
    "2Y": 24,
    "3Y": 36,
    "4Y": 48,
    "5Y": 60,
}

records = []
for entry in entry_dates:
    nav_start = df.loc[entry, "nav"]
    for label, months in holding_periods.items():
        exit_target = entry + pd.DateOffset(months=months)
        future = df.loc[df.index >= exit_target, "nav"]
        if future.empty:
            continue
        nav_end = future.iloc[0]
        years = months / 12
        # ❌ WRONG FORMULA — this is absolute return, NOT CAGR
        # Must be replaced with: ((nav_end / nav_start) ** (1 / years) - 1) * 100
        cagr = ((nav_end - nav_start) / nav_start) * 100
        records.append({
            "start_date": entry,
            "holding_period": label,
            "CAGR": cagr
        })

sim_df = pd.DataFrame(records)
average_cagr = sim_df["CAGR"].mean()



#############################


import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, no_update
from datetime import datetime

# ----------------------------
# Preprocessing (ONE-TIME)
# ----------------------------
sim_df["start_date"] = pd.to_datetime(sim_df["start_date"], errors="coerce")

# Stable holding period order
ORDER = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "4Y", "5Y"]
sim_df["holding_period"] = pd.Categorical(sim_df["holding_period"], categories=ORDER, ordered=True)

# AbsReturn: currently same as CAGR (placeholder)
if "AbsReturn" not in sim_df.columns:
    sim_df["AbsReturn"] = sim_df["CAGR"]

# Vectorized end_date computation
hp = sim_df["holding_period"].astype(str)
is_months = hp.str.endswith("M")
is_years  = hp.str.endswith("Y")

months = pd.to_numeric(hp.str.replace("M", "", regex=False), errors="coerce").fillna(0).astype(int)
years  = pd.to_numeric(hp.str.replace("Y", "", regex=False), errors="coerce").fillna(0).astype(int)

month_offsets = pd.to_timedelta(months * 30, unit="D")
end_date = np.where(
    is_months.values,
    sim_df["start_date"] + month_offsets,
    np.where(is_years.values, sim_df["start_date"] + pd.to_timedelta(years * 365, unit="D"), sim_df["start_date"])
)
sim_df["end_date"] = pd.to_datetime(end_date)

AVAILABLE_YEARS = sorted(sim_df["start_date"].dt.year.dropna().unique().tolist())
DEFAULT_YEAR = int(datetime.now().year) if len(AVAILABLE_YEARS) == 0 else AVAILABLE_YEARS[-1]

# ----------------------------
# Dash App — REPLACE WITH FASTAPI + REACT
# ----------------------------
app = Dash(__name__)

app.layout = html.Div(
    [
        html.H2("Interactive Abs. Return vs Holding Period"),
        html.Label("Select Year:"),
        dcc.Dropdown(
            id="year-selector",
            options=[{"label": str(y), "value": int(y)} for y in AVAILABLE_YEARS],
            value=DEFAULT_YEAR,
            clearable=False,
        ),
        dcc.Graph(id="cagr-chart"),
    ],
    style={"maxWidth": 1100, "margin": "0 auto"}
)

@app.callback(
    Output("cagr-chart", "figure"),
    Input("year-selector", "value")
)
def update_chart(selected_year: int):
    if selected_year is None or sim_df.empty:
        return no_update

    df = sim_df.copy(False)
    year_series = df["start_date"].dt.year
    df["YearCategory"] = np.where(year_series == selected_year, "Selected Year", "Other Years")

    fig = px.scatter(
        df,
        x="holding_period",
        y="CAGR",
        color="YearCategory",
        color_discrete_map={"Selected Year": "blue", "Other Years": "#97144d"},
        category_orders={"holding_period": ORDER, "YearCategory": ["Selected Year", "Other Years"]},
        custom_data=["AbsReturn", "start_date", "end_date"],
        title=f"CAGR vs Holding Period (Highlight investors who start in {selected_year})",
        labels={
            "holding_period": "Holding Period",
            "CAGR": "Abs. Returns (%)",
            "YearCategory": "Year Group"
        },
        hover_data=None
    )

    fig.update_traces(
        hovertemplate=(
            "Abs. Return: %{customdata[0]:.2f}%<br>"
            "Start Date: %{customdata[1]|%d-%m-%Y}<br>"
            "End Date: %{customdata[2]|%d-%m-%Y}<br>"
            "<extra></extra>"
        )
    )

    # Selected-year bands (min/max) per holding period
    sel = df[df["YearCategory"] == "Selected Year"]
    if not sel.empty:
        band = (
            sel.groupby("holding_period", observed=True)["CAGR"]
            .agg(y_min="min", y_max="max")
            .reindex(ORDER)
            .dropna()
            .reset_index()
        )

        if not band.empty:
            # Green shaded area (min to max for selected year)
            fig.add_trace(
                go.Scatter(
                    x=band["holding_period"],
                    y=band["y_min"],
                    mode="lines",
                    line=dict(width=0),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=band["holding_period"],
                    y=band["y_max"],
                    mode="lines",
                    fill="tonexty",
                    fillcolor="rgba(0,128,0,0.25)",
                    line=dict(width=0),
                    name="Selected Year Range",
                )
            )

            # Red area for negative returns within selected year
            neg = sel[sel["CAGR"] < 0]
            if not neg.empty:
                neg_band = (
                    neg.groupby("holding_period", observed=True)["CAGR"]
                    .agg(y_neg_min="min", y_neg_max="max")
                    .reindex(ORDER)
                    .dropna()
                    .reset_index()
                )
                if not neg_band.empty:
                    neg_merged = neg_band.merge(band, on="holding_period", how="left")
                    y_top = np.minimum(0, neg_merged["y_max"].fillna(0))

                    fig.add_trace(
                        go.Scatter(
                            x=neg_merged["holding_period"],
                            y=y_top,
                            mode="lines",
                            line=dict(width=0),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=neg_merged["holding_period"],
                            y=neg_merged["y_neg_min"],
                            mode="lines",
                            fill="tonexty",
                            fillcolor="rgba(255,0,0,0.3)",
                            line=dict(width=0),
                            name="Negative Return Area",
                        )
                    )

    # Mean line (overall)
    mean_cagr = df["CAGR"].mean()
    fig.add_hline(
        y=mean_cagr,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Mean Abs. Return: {mean_cagr:.2f}%",
        annotation_position="top left",
    )

    fig.update_layout(
        template="plotly_white",
        xaxis_title="Holding Period",
        yaxis_title="Abs. Returns (%)",
        legend=dict(title="Year Group"),
        margin=dict(l=40, r=20, t=70, b=40),
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True)
```

-----

## Build Sequence — Phase by Phase

### Phase 1 — Mock Data + Single Fund Chart

**Goal:** Get one fund’s dot plot working correctly with proper CAGR formula before adding any complexity.

Steps:

1. Create mock portfolio with 3 funds:
- Fund A: “Axis Small Cap Fund” — equity, scheme_code 120503
- Fund B: “HDFC Corporate Bond Fund” — debt, scheme_code 101385
- Fund C: “ICICI Pru Balanced Advantage Fund” — hybrid, scheme_code 120594
- Weights: 60% / 25% / 15%
- Fetch real historical NAV from MFapi for all three
1. Fix CAGR formula — replace absolute return with correct CAGR
1. Build simulation loop for single fund — first trading day of each month as entry dates
1. Manually verify 3-4 data points by hand before proceeding
1. Build React frontend with Plotly dot plot for single fund
1. Validate visually — spread should be widest at 1M and narrowest at 5Y

**Validation checkpoint:** Manually calculate CAGR for one entry date at one holding period and confirm it matches the chart dot.

-----

### Phase 2 — Blended Portfolio Chart

**Goal:** Combine all three mock funds into one blended portfolio dot plot.

Steps:

1. Implement blending formula: `Σ(weight_i × nav_end_i / nav_start_i)`
1. Apply CAGR on blended ratio
1. Handle missing data — if one fund has no NAV on entry date, skip that entry date
1. Add holding period slider to frontend
1. Grey out fund contributions where history is insufficient
1. Add risk metric: % of negative entry points per holding period
1. Add mean CAGR line
1. Add red shaded area for negative returns
1. Add summary note in comparison framing

**Validation checkpoint:** Pick one entry date, manually calculate blended CAGR for 3Y holding period, confirm it matches chart.

-----

### Phase 3 — User Entry Point + Cohort Highlight

**Goal:** Personalise the chart with the user’s own entry point and cohort comparison.

Steps:

1. Accept user’s entry date as input (mock input for now — real CAS in Phase 5)
1. Highlight user’s entry year dots in blue
1. Add green band (min-max range for user’s entry year)
1. Compute cohort risk at three levels — same year, same quarter, same month
1. Show most precise cohort with sufficient data (minimum 3 entry points)
1. Add cohort tooltip on user’s dot
1. Build opening statement from cohort data

-----

### Phase 4 — Progressive Disclosure + Full Mobile UI

**Goal:** Build the complete mobile-optimised UI with all three layers.

Steps:

1. Mobile-first layout with Tailwind — max-width 430px, touch optimised
1. Layer 1: Opening statement — bold, above the fold, no scroll required
1. Layer 2: CTA button *“See your risk chart”* — reveals dot plot on tap
1. Individual fund charts — one per fund, scrollable
1. Blended portfolio chart — with slider
1. Layer 3: Collapsible *“Why does this fund behave this way?”* sections
1. Risk contribution breakdown — ranked list
1. Persistent disclaimer footer
1. Test on mobile viewport — all interactions must work on touch

-----

### Phase 5 — CAS PDF Parser

**Goal:** Replace mock data with real user portfolio data from CAS PDF.

Steps:

1. Build PDF upload interface in React
1. Build FastAPI endpoint: `POST /parse-cas`
- Accept PDF file + PAN + DOB
- Construct password: first 4 chars of PAN uppercase + DOB as DDMMYYYY
- Unlock PDF using pdfplumber
- Extract transaction history — fund name, transaction type (buy/sell/SIP), units, date
- Derive current units per fund: sum(buy units) - sum(sell units)
- Map fund names to MFapi scheme codes using fuzzy matching (use rapidfuzz library)
- Fetch latest NAV from MFapi per fund
- Compute current market value: current units × latest NAV
- Compute weights: market_value_i / total_portfolio_value
- Return structured JSON: list of funds with scheme_code, weight, entry_date, current_value
1. Connect parser output to simulation engine
1. Test with real CAS PDF — validate parsed holdings match what user sees on Groww/Zerodha
1. Handle edge cases:
- Fund name in CAS does not exactly match MFapi name — use fuzzy matching
- Fund has been fully redeemed — exclude from portfolio
- Fund switched from regular to direct plan — treat as new fund entry

-----

### Phase 6 — NAV Caching + Performance

**Goal:** Ensure the tool loads fast on mobile, does not hammer MFapi.

Steps:

1. Cache NAV data in memory per session — fetch once, reuse
1. Fetch all required fund NAVs in parallel — not sequentially
1. Show loading skeleton UI while simulation runs
1. Target: results visible within 5 seconds of PDF upload on mobile

-----

### Phase 7 — Deployment

**Goal:** Deploy to Railway, accessible via public URL.

Steps:

1. Set up GitHub repository
1. Configure Railway project — React frontend + FastAPI backend
1. Set environment variables
1. Deploy and test on real mobile device
1. Test with real CAS PDF end to end

-----

## Important Instructions for Claude Code

1. **Never store PAN, DOB, or any user data** — process in memory only, discard after session
1. **CAGR formula is critical** — double check every computation, the existing code has it wrong
1. **Mobile first** — every UI decision optimises for 375px-430px screen width first
1. **Plain language always** — no financial jargon in any user-facing text
1. **Honest about limitations** — grey out insufficient data, never extrapolate silently
1. **No buy/sell recommendations** — this is a risk visualisation tool, not an advisory tool
1. **Rate limit MFapi** — cache aggressively, never fetch the same NAV history twice in a session
1. **Fuzzy match fund names** — CAS fund names and MFapi fund names will not always match exactly, use rapidfuzz
1. **Test CAGR manually** — before proceeding from Phase 1, manually verify at least 3 data points
1. **Do not proceed to next phase without explicit confirmation** — complete each phase, present output, wait for sign-off before moving forward

-----

## Validation Checklist Before Each Phase Sign-off

- [ ] CAGR formula produces correct numbers (verified manually)
- [ ] Blending formula matches Groww portfolio value (verified manually)
- [ ] Risk metric (% negative) computed correctly per holding period
- [ ] Spread visually narrows at longer holding periods
- [ ] Red area correctly bounded below zero
- [ ] Mobile layout works on 375px viewport
- [ ] No user data stored or logged
- [ ] Disclaimer visible on all screens
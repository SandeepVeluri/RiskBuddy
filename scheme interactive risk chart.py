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
# Ensure start_date is datetime
sim_df["start_date"] = pd.to_datetime(sim_df["start_date"], errors="coerce")

# Stable holding period order
ORDER = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "4Y", "5Y"]
sim_df["holding_period"] = pd.Categorical(sim_df["holding_period"], categories=ORDER, ordered=True)

# AbsReturn: currently same as CAGR (placeholder)
# TIP: if you want absolute return, replace this with a correct formula.
if "AbsReturn" not in sim_df.columns:
    sim_df["AbsReturn"] = sim_df["CAGR"]

# Vectorized end_date computation
hp = sim_df["holding_period"].astype(str)
is_months = hp.str.endswith("M")
is_years  = hp.str.endswith("Y")

months = pd.to_numeric(hp.str.replace("M", "", regex=False), errors="coerce").fillna(0).astype(int)
years  = pd.to_numeric(hp.str.replace("Y", "", regex=False), errors="coerce").fillna(0).astype(int)

month_offsets = pd.to_timedelta(months * 30, unit="D")  # fast approx; switch to DateOffset if exact month logic is required
# If you need *exact* month/year rollovers, uncomment below and comment timedelta lines.
# month_offsets_exact = [pd.DateOffset(months=m) for m in months]
# year_offsets_exact = [pd.DateOffset(years=y) for y in years]

end_date = np.where(
    is_months.values,
    sim_df["start_date"] + month_offsets,
    np.where(is_years.values, sim_df["start_date"] + pd.to_timedelta(years * 365, unit="D"), sim_df["start_date"])
)
sim_df["end_date"] = pd.to_datetime(end_date)

# Year options once
AVAILABLE_YEARS = sorted(sim_df["start_date"].dt.year.dropna().unique().tolist())
DEFAULT_YEAR = int(datetime.now().year) if len(AVAILABLE_YEARS) == 0 else AVAILABLE_YEARS[-1]

# ----------------------------
# Dash App
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

    # Create a view (do not mutate sim_df)
    df = sim_df.copy(False)
    year_series = df["start_date"].dt.year
    df["YearCategory"] = np.where(year_series == selected_year, "Selected Year", "Other Years")

    # Base scatter
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
        hover_data=None  # we'll define a clean template below
    )

    # Clean hover template with real HTML line breaks
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
            # Green shaded area (min..max)
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

            # Negative area bounded within green area up to 0
            neg = sel[sel["CAGR"] < 0]
            if not neg.empty:
                neg_band = (
                    neg.groupby("holding_period", observed=True)["CAGR"]
                    .agg(y_neg_min="min", y_neg_max="max")  # y_neg_max will be <= 0
                    .reindex(ORDER)
                    .dropna()
                    .reset_index()
                )
                if not neg_band.empty:
                    # Top for negative area = min(0, green y_max) where available
                    # Merge to cap by green band
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
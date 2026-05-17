import pandas as pd

HOLDING_PERIODS = {
    "1M": 1,
    "3M": 3,
    "6M": 6,
    "1Y": 12,
    "2Y": 24,
    "3Y": 36,
    "4Y": 48,
    "5Y": 60,
}
ORDER = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "4Y", "5Y"]


def simulate_single_fund(df: pd.DataFrame) -> list[dict]:
    first_trades = df.groupby(df.index.to_period("M")).apply(
        lambda grp: grp.index.min()
    )
    entry_dates = first_trades.tolist()

    records: list[dict] = []
    for entry in entry_dates:
        nav_start = df.loc[entry, "nav"]
        for label, months in HOLDING_PERIODS.items():
            exit_target = entry + pd.DateOffset(months=months)
            future = df.loc[df.index >= exit_target, "nav"]
            if future.empty:
                continue
            nav_end = future.iloc[0]
            exit_date = future.index[0]
            years = months / 12
            cagr = ((nav_end / nav_start) ** (1 / years) - 1) * 100
            abs_return = ((nav_end - nav_start) / nav_start) * 100
            records.append(
                {
                    "start_date": entry.strftime("%Y-%m-%d"),
                    "end_date": exit_date.strftime("%Y-%m-%d"),
                    "holding_period": label,
                    "cagr": round(float(cagr), 4),
                    "abs_return": round(float(abs_return), 4),
                }
            )
    return records


def simulate_portfolio(
    funds_data: list[dict],
) -> tuple[list[dict], dict[str, list[str]]]:
    """
    funds_data: list of {"df": pd.DataFrame, "code": str, "weight": float}

    Blended formula per entry+period:
        ratio = Σ(weight_i × nav_end_i / nav_start_i)
        CAGR  = (ratio ^ (1/years) - 1) × 100

    Skips any entry+period where a fund has no NAV data (not yet launched or
    history too short). Tracks which funds caused skips per period.
    """
    primary_df = max(funds_data, key=lambda f: len(f["df"]))["df"]
    first_trades = primary_df.groupby(primary_df.index.to_period("M")).apply(
        lambda grp: grp.index.min()
    )
    entry_dates = sorted(first_trades.tolist())

    records: list[dict] = []
    period_missing: dict[str, set[str]] = {label: set() for label in HOLDING_PERIODS}

    for entry in entry_dates:
        for label, months in HOLDING_PERIODS.items():
            exit_target = entry + pd.DateOffset(months=months)
            years = months / 12
            blended_ratio = 0.0
            skip = False
            exit_date = None

            for fund in funds_data:
                df, code, weight = fund["df"], fund["code"], fund["weight"]

                start_slice = df.loc[df.index <= entry, "nav"]
                if start_slice.empty:
                    period_missing[label].add(code)
                    skip = True
                    break
                nav_start = start_slice.iloc[-1]

                end_slice = df.loc[df.index >= exit_target, "nav"]
                if end_slice.empty:
                    period_missing[label].add(code)
                    skip = True
                    break
                nav_end = end_slice.iloc[0]

                if exit_date is None:
                    exit_date = end_slice.index[0]

                blended_ratio += weight * (nav_end / nav_start)

            if skip:
                continue

            cagr = (blended_ratio ** (1 / years) - 1) * 100
            abs_return = (blended_ratio - 1) * 100
            records.append(
                {
                    "start_date": entry.strftime("%Y-%m-%d"),
                    "end_date": exit_date.strftime("%Y-%m-%d"),
                    "holding_period": label,
                    "cagr": round(float(cagr), 4),
                    "abs_return": round(float(abs_return), 4),
                }
            )

    insufficient = {k: sorted(v) for k, v in period_missing.items() if v}
    return records, insufficient

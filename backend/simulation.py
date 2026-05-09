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

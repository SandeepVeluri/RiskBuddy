import httpx
import pandas as pd

MFAPI_BASE = "https://api.mfapi.in"
_NAV_CACHE: dict[str, pd.DataFrame] = {}


def fetch_nav_history(scheme_code: str) -> pd.DataFrame:
    if scheme_code in _NAV_CACHE:
        return _NAV_CACHE[scheme_code]

    url = f"{MFAPI_BASE}/mf/{scheme_code}"
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        payload = resp.json()

    raw = payload.get("data") or []
    if not raw:
        raise ValueError(f"No NAV data returned for scheme {scheme_code}")

    df = pd.DataFrame(raw)
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["nav", "date"]).set_index("date").sort_index()

    _NAV_CACHE[scheme_code] = df
    return df


def clear_cache() -> None:
    _NAV_CACHE.clear()

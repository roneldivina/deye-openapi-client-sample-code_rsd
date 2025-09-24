from datetime import date, timedelta
from clientcode.obtain_token import get_token
import requests
from urllib.parse import urljoin

API_BASE = "https://eu1-developer.deyecloud.com/v1.0"

def fetch_monthly_stats(plant_id: str, start_dt: date, end_dt: date, token: str) -> dict:
    """
    Try the “monthly” stats endpoint first; if fails, fall back to daily loop.
    Returns a dict:
      {
        "generation": float,
        "grid_import": float,
        "grid_export": float,
        "consumption": float or None
      }
    """
    headers = {"Authorization": f"Bearer {token}"}
    url_monthly = urljoin(API_BASE, f"/v1/plant/{plant_id}/monthly")
    params = {
        "startDate": start_dt.isoformat(),
        "endDate": end_dt.isoformat()
    }
    try:
        r = requests.get(url_monthly, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            j = r.json()
            data = j.get("data") or {}
            return {
                "generation": float(data.get("generation", 0)),
                "grid_import": float(data.get("gridImport", 0)),
                "grid_export": float(data.get("gridExport", 0)),
                "consumption": (float(data["consumption"]) if data.get("consumption") is not None else None)
            }
    except Exception as e:
        # log or swallow and fall back
        print("Monthly endpoint failed:", e)

    # fallback: daily aggregation
    total_gen = total_imp = total_exp = 0.0
    total_cons = 0.0
    have_cons = False

    cur = start_dt
    while cur <= end_dt:
        url_daily = urljoin(API_BASE, f"/v1/plant/{plant_id}/daily")
        params = {"date": cur.isoformat()}
        r = requests.get(url_daily, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        j = r.json().get("data") or {}
        total_gen += float(j.get("generation", 0))
        total_imp += float(j.get("gridImport", 0))
        total_exp += float(j.get("gridExport", 0))
        if j.get("consumption") is not None:
            have_cons = True
            total_cons += float(j.get("consumption"))
        cur += timedelta(days=1)

    return {
        "generation": round(total_gen, 3),
        "grid_import": round(total_imp, 3),
        "grid_export": round(total_exp, 3),
        "consumption": (round(total_cons, 3) if have_cons else None)
    }

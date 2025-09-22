import requests
import pandas as pd
from datetime import datetime, timedelta
from clientcode import variable

# -------------------------
# CONFIG
# -------------------------
USERNAME = "engrdivina@writeshopsolar.com"
PASSWORD = "pece01@01"
DEVICE_SN = "2505240025"
TARIFF = 12       # Local rate (₱/kWh)
EXPORT_TARIFF = 6 # Grid export rate (₱/kWh)

BASE_URL = "https://eu1-developer.deyecloud.com/v1.0"

# -------------------------
# 1. LOGIN to get token
# -------------------------
def get_token():
    url = f"{BASE_URL}/user/login"
    payload = {"username": USERNAME, "password": PASSWORD}
    res = requests.post(url, json=payload).json()
    print("Login response:", res)  # 👈 add this line
    # return res["data"]["token"]
    if "data" in res and "token" in res["data"]:
        return res["data"]["token"]
    else:
        raise Exception(f"Login failed: {res}")

# -------------------------
# 2. GET DEVICE DATA
# -------------------------
def get_device_data(token):
    url = f"{BASE_URL}/device/data"
    params = {"sn": DEVICE_SN, "token": token}
    res = requests.get(url, params=params).json()
    return res["data"]

# -------------------------
# 3. PROCESS & CALCULATE SAVINGS
# -------------------------
def calculate_savings(data):
    pv_today = data.get("pvEnergyToday", 0)
    grid_export = data.get("gridExportToday", 0)

    self_consumption = pv_today - grid_export
    grid_savings = self_consumption * TARIFF
    export_income = grid_export * EXPORT_TARIFF
    total_savings = grid_savings + export_income

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "pvEnergyToday": pv_today,
        "gridExportToday": grid_export,
        "selfConsumption": self_consumption,
        "gridSavings": grid_savings,
        "exportIncome": export_income,
        "totalSavings": total_savings
    }

# -------------------------
# 4. SAVE TO CSV/EXCEL
# -------------------------
def save_to_excel(record, filename="deye_savings.xlsx"):
    try:
        df = pd.read_excel(filename)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "date","pvEnergyToday","gridExportToday",
            "selfConsumption","gridSavings","exportIncome","totalSavings"
        ])
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_excel(filename, index=False)

# -------------------------
# MAIN SCRIPT
# -------------------------
if __name__ == "__main__":
    token = get_token()
    data = get_device_data(token)
    record = calculate_savings(data)
    save_to_excel(record)
    print("✅ Record saved:", record)

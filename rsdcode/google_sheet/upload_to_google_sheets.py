import requests
from clientcode import variable
from pprint import pprint
import gspread
from google.oauth2.service_account import Credentials


# (key=API_KEY)AIzaSyCmgWkBb_bmsK0CpCyL1pl1JAencoI7BKw

# --- Google Sheets setup ---
# Path to your service account credentials file
SERVICE_ACCOUNT_FILE = 'path/to/your/credentials.json'
# Name of your Google Sheet
SPREADSHEET_NAME = 'SolarSavings'

# Authenticate and open the sheet
scopes = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
gc = gspread.authorize(credentials)
sh = gc.open(SPREADSHEET_NAME)
worksheet = sh.sheet1  # Use the first sheet

# --- API request ---
url = variable.baseurl + '/device/history'
headers = variable.headers

data = {
    "deviceSn": "2505240025",
    "granularity": 4,
    "startAt": "2025",
    "endAt": "2025",
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
pprint(result)

# Extract and export
try:
    device_sn = result.get('deviceSn', 'N/A')
    month = result['dataList'][0]['time']  # e.g., '2025'
    item_list = result['dataList'][0]['itemList']
    production = next(item for item in item_list if item['name'] == 'Production')
    production_value = float(production['value'])
    savings = production_value * 11.15

    # Prepare row
    row = [device_sn, month, f"{production_value:.2f}", f"{savings:.2f}"]

    # Optional: add header if sheet is empty
    if len(worksheet.get_all_values()) == 0:
        worksheet.append_row(['DeviceSn', 'Month', 'Production (kWh)', 'Savings (PHP)'])

    worksheet.append_row(row)
    print(f"Exported to Google Sheets: {row}")

except Exception as e:
    print("Could not export savings:", e)
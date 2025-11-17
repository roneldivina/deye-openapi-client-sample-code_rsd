"""
Master script: combines all clientcode modules into one file
"""

import requests
from pprint import pprint
from datetime import datetime, timezone, date
from clientcode import variable
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# ========================
# 1. Station Alert List
# ========================

def get_station_alerts():
    """Fetch and display station alerts with human-readable timestamps"""
    url = variable.baseurl + '/station/alertList'
    headers = dict(variable.headers) if hasattr(variable, 'headers') else {}
    headers.setdefault('Content-Type', 'application/json')

    def to_ts(date_str, fmt='%Y-%m-%d'):
        dt = datetime.strptime(date_str, fmt)
        return int(dt.replace(tzinfo=timezone.utc).timestamp())

    data = {
        "stationId": 61553118,
        "startTimestamp": to_ts("2025-10-18"),
        "endTimestamp": to_ts("2025-10-19"),
        "page": 1,
        "size": 1
    }

    print("\n=== Station Alerts ===")
    print("Request payload:")
    pprint(data)

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")

    try:
        j = response.json()

        def format_ts_debug(ts):
            if ts is None:
                return None
            ts = int(ts)
            dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
            dt_local = dt_utc.astimezone()
            return {
                "epoch": ts,
                "utc_iso": dt_utc.isoformat(),
                "local_iso": dt_local.isoformat(),
                "local_repr": dt_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')
            }

        items = j.get('stationAlertItems')
        if items:
            for it in items:
                it['alertStartTime_debug'] = format_ts_debug(it.get('alertStartTime'))
                it['alertEndTime_debug'] = format_ts_debug(it.get('alertEndTime'))

        pprint(j)
    except ValueError:
        print(response.text)


# ========================
# 2. Brevo Email Campaign
# ========================

def create_brevo_campaign():
    """Create and send email campaign via Brevo with overall production & savings only"""
    # NOTE: Keep your API_KEY here (it was in your original script)
    API_KEY = "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"

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = API_KEY

    api_instance = sib_api_v3_sdk.EmailCampaignsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    # ========================
    # Fetch Overall Production from device/history
    # ========================
    device_sn = "2505240025"  # from the snippet you provided
    url_device_history = variable.baseurl + '/device/history'
    headers = dict(variable.headers) if hasattr(variable, 'headers') else {}
    headers.setdefault('Content-Type', 'application/json')

    data = {
        "deviceSn": device_sn,
        # the snippet used granularity 4 and year-range; keep the same
        "granularity": 4,
        "startAt": "2025",
        "endAt": "2025",
    }

    print("\n=== Fetching device history for Production ===")
    print("Request payload:")
    pprint(data)

    production_value = 0.0
    RATE_PER_KWH = 11.15  # PHP per kWh

    try:
        resp = requests.post(url_device_history, headers=headers, json=data)
        print(f"device/history status: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            # attempt to extract the production item value
            try:
                item_list = result['dataList'][0]['itemList']
                production_item = next((item for item in item_list if item.get('name') == 'Production'), None)
                if production_item is not None:
                    production_value = float(production_item.get('value') or 0)
                    print(f"Extracted Production: {production_value} kWh")
                else:
                    print("Production item not found in device history response.")
                    pprint(result)
            except Exception as e:
                print("Error extracting Production from device history response:", e)
                pprint(result)
        else:
            print("Error fetching device history:", resp.status_code, resp.text)
    except Exception as e:
        print("Request to device/history failed:", e)

    # ========================
    # Calculate Savings (only overall)
    # ========================
    overall_production = production_value
    overall_savings = overall_production * RATE_PER_KWH

    print(f"Overall Production: {overall_production:,.2f} kWh")
    print(f"Overall Savings: PHP {overall_savings:,.2f}")

    # ========================
    # Create Campaign with only Overall Production & Savings
    # ========================
    today = date.today()
    html_content = f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #fa2d39; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                .box {{ background-color: #f7f7f7; padding: 20px; margin: 20px 0; border-radius: 5px; text-align: center; }}
                .amount {{ font-size: 28px; font-weight: bold; margin-top: 10px; }}
                .label {{ color: #555; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>☀️ Overall Solar Production & Savings</h1>
                </div>

                <div class="box">
                    <div class="label">Overall Production (kWh)</div>
                    <div class="amount">{overall_production:,.2f} kWh</div>

                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">

                    <div class="label">Overall Savings (PHP)</div>
                    <div class="amount">PHP {overall_savings:,.2f}</div>
                </div>

                <p style="text-align:center; color:#777; font-size:13px;">Report generated on {today.strftime('%Y-%m-%d')}</p>
                <p style="text-align:center;"><strong>Writeshop Solar Team</strong></p>
            </div>
        </body>
        </html>
    """

    # Prepare campaign object: only change content and subject to show overall savings
    email_campaign = sib_api_v3_sdk.CreateEmailCampaign(
        name="Overall Solar Savings Report - " + today.strftime('%B %Y'),
        subject=f"Your Overall Solar Savings: PHP {overall_savings:,.2f}",
        sender={
            "name": "Writeshop Solar",
            "email": "hello@marketing.writeshopsolar.com"
        },
        html_content=html_content,
        recipients={"listIds": [2, 7]},
        scheduled_at="2025-11-17 14:21:01"  # keep existing scheduled time (modify as needed)
    )

    print("\n=== Brevo Campaign ===")
    try:
        api_response = api_instance.create_email_campaign(email_campaign)
        print("Campaign created successfully!")
        pprint(api_response)
    except ApiException as e:
        print("Error calling EmailCampaignsApi->create_email_campaign: %s\n" % e)


# ========================
# Main Entry Point
# ========================

if __name__ == '__main__':
    print("Starting combined operations...\n")

    # Run station alerts
    get_station_alerts()

    # Run Brevo campaign
    create_brevo_campaign()

    print("\n=== All operations completed ===")

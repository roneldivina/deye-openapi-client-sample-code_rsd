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
# 1. Station Alert List (debug function kept)
# ========================

def get_station_alerts():
    """Fetch and display station alerts with human-readable timestamps (unchanged)"""
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

    print("\n=== Station Alerts (Debug) ===")
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
# 2. Brevo Email Campaign (with production + latest alert)
# ========================

def create_brevo_campaign():
    """Create and send email campaign via Brevo with overall production, savings, greeting, and latest error box"""
    API_KEY = "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"

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = API_KEY

    api_instance = sib_api_v3_sdk.EmailCampaignsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    RATE_PER_KWH = 11.15  # PHP per kWh

    # ------------------------
    # A) Fetch Overall Production from device/history
    # ------------------------
    device_sn = "2505240025"
    url_device_history = variable.baseurl + '/device/history'
    headers = dict(variable.headers) if hasattr(variable, 'headers') else {}
    headers.setdefault('Content-Type', 'application/json')

    data_history = {
        "deviceSn": device_sn,
        "granularity": 4,
        "startAt": "2025",
        "endAt": "2025",
    }

    print("\n=== Fetching device history for Production ===")
    pprint(data_history)

    production_value = 0.0
    try:
        resp = requests.post(url_device_history, headers=headers, json=data_history, timeout=20)
        print(f"device/history status: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
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

    overall_production = production_value
    overall_savings = overall_production * RATE_PER_KWH

    # ------------------------
    # B) Fetch latest 3 alerts from station/alertList, choose most recent one
    # ------------------------
    url_alerts = variable.baseurl + '/station/alertList'
    headers_alerts = dict(variable.headers) if hasattr(variable, 'headers') else {}
    headers_alerts.setdefault('Content-Type', 'application/json')

    def to_ts(date_str, fmt='%Y-%m-%d'):
        dt = datetime.strptime(date_str, fmt)
        return int(dt.replace(tzinfo=timezone.utc).timestamp())

    # fetch 3 latest alerts
    data_alerts = {
        "stationId": 61553118,
        # wide range to ensure we get recent items; adjust as needed
        "startTimestamp": to_ts("2025-10-18"),
        "endTimestamp": to_ts("2025-12-30"),
        "page": 1,
        "size": 3
    }

    print("\n=== Fetching latest 3 station alerts ===")
    pprint(data_alerts)

    latest_alert = None
    try:
        resp_alerts = requests.post(url_alerts, headers=headers_alerts, json=data_alerts, timeout=20)
        print("station/alertList status:", resp_alerts.status_code)
        if resp_alerts.status_code == 200:
            alerts_json = resp_alerts.json()
            items = alerts_json.get('stationAlertItems') or []
            # Sort by alertStartTime descending to ensure most recent first
            try:
                items_sorted = sorted(items, key=lambda x: int(x.get('alertStartTime') or 0), reverse=True)
            except Exception:
                items_sorted = items
            if items_sorted:
                latest_alert = items_sorted[0]
                print("Latest alert extracted:")
                pprint(latest_alert)
            else:
                print("No alerts returned.")
                latest_alert = None
        else:
            print("Error fetching alerts:", resp_alerts.status_code, resp_alerts.text)
    except Exception as e:
        print("Request to station/alertList failed:", e)

    # Interpret latest alert fields
    alert_name = None
    alert_status_text = None
    alert_status_dot_color = None  # hex color for dot
    alert_start_hr_local = None

    if latest_alert:
        alert_name = latest_alert.get('alertName') or latest_alert.get('alertCode') or 'Unknown'
        status_val = latest_alert.get('status')
        # status mapping: 0 -> Resolved, else -> On-going
        try:
            status_int = int(status_val)
        except Exception:
            status_int = None

        if status_int == 0:
            alert_status_text = "Resolved"
            alert_status_dot_color = "#2ecc71"  # green
        else:
            alert_status_text = "On-going"
            alert_status_dot_color = "#e74c3c"  # red

        # optional formatted local time if available (API might already include)
        alert_start_hr_local = latest_alert.get('alertStartTime_hr_local')
        if not alert_start_hr_local and latest_alert.get('alertStartTime') is not None:
            try:
                ts = int(latest_alert.get('alertStartTime'))
                alert_start_hr_local = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                alert_start_hr_local = None

    # ------------------------
    # C) Build Email HTML (Greeting + Overall Production/Savings + Latest Error box)
    # ------------------------
    today = date.today()
    # ensure theme color #fa2d39 used as header (user preference)
    header_color = "#fa2d39"

    # status dot HTML (if no alert, show N/A)
    if alert_name:
        status_dot_html = f"""<span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:{alert_status_dot_color}; margin-right:8px; vertical-align:middle;"></span>"""
        alert_time_line = f"<div class='label small'>Time: {alert_start_hr_local}</div>" if alert_start_hr_local else ""
    else:
        status_dot_html = ""
        alert_time_line = ""

    html_content = f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; margin:0; padding:0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {header_color}; color: white; padding: 18px; text-align: center; border-radius: 6px; }}
                .greeting {{ margin-top: 18px; font-size: 16px; }}
                .box {{ background-color: #f7f7f7; padding: 18px; margin: 18px 0; border-radius: 6px; text-align: center; }}
                .label {{ color: #555; font-size: 14px; }}
                .amount {{ font-size: 24px; font-weight: bold; margin-top: 8px; }}
                .error-box {{ background: #fff; border: 1px solid #e6e6e6; border-radius: 6px; padding: 16px; margin: 18px 0; }}
                .error-title {{ font-size: 16px; margin-bottom: 8px; }}
                .error-name {{ font-weight: 600; color: #333; margin-bottom: 6px; }}
                .error-status {{ font-size: 15px; color: #333; vertical-align: middle; }}
                .small {{ font-size: 13px; color:#777; }}
                hr.sep {{ border: none; border-top: 1px solid #eee; margin: 18px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0; font-size:20px;">☀️ Overall Solar Production & Savings</h1>
                </div>

                <div class="greeting">
                    <p style="margin:0 0 12px 0; font-size:15px;">Hello,</p>
                </div>

                <div class="box" role="region" aria-label="Savings">
                    <div class="label">Overall Production (kWh)</div>
                    <div class="amount">{overall_production:,.2f} kWh</div>

                    <hr class="sep">

                    <div class="label">Overall Savings (PHP)</div>
                    <div class="amount">PHP {overall_savings:,.2f}</div>
                </div>

                <div class="error-box" role="region" aria-label="Latest Error">
                    <div class="error-title small">Latest Error</div>
                    <div class="error-name">{alert_name if alert_name else 'No recent alerts'}</div>
                    {alert_time_line}
                    <div style="height:8px;"></div>
                    <div class="error-status">
                        {status_dot_html}
                        <span style="vertical-align:middle;">{alert_status_text if alert_status_text else 'N/A'}</span>
                    </div>
                </div>

                <p style="text-align:center; color:#777; font-size:12px;">Report generated on {today.strftime('%Y-%m-%d')}</p>
                <p style="text-align:center;"><strong>Writeshop Solar Team</strong></p>
            </div>
        </body>
        </html>
    """

    # ------------------------
    # D) Create and schedule the campaign
    # ------------------------
    email_campaign = sib_api_v3_sdk.CreateEmailCampaign(
        name="Overall Solar Savings Report - " + today.strftime('%B %Y'),
        subject=f"Your Overall Solar Savings: PHP {overall_savings:,.2f}",
        sender={
            "name": "Writeshop Solar",
            "email": "hello@marketing.writeshopsolar.com"
        },
        html_content=html_content,
        recipients={"listIds": [2, 7]},
        scheduled_at="2025-11-17 13:51:01"  # keep existing scheduled time (modify as needed)
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

    # Run station alerts (debug)
    get_station_alerts()

    # Run Brevo campaign
    create_brevo_campaign()

    print("\n=== All operations completed ===")

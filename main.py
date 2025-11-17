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
    """Create and send email campaign via Brevo with energy savings calculation"""
    API_KEY = "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"

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = API_KEY

    api_instance = sib_api_v3_sdk.EmailCampaignsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    # ========================
    # Fetch Energy Data
    # ========================
    url_energy = variable.baseurl + '/station/energyStatistic'
    headers = dict(variable.headers) if hasattr(variable, 'headers') else {}
    headers.setdefault('Content-Type', 'application/json')

    def to_ts(date_str, fmt='%Y-%m-%d'):
        dt = datetime.strptime(date_str, fmt)
        return int(dt.replace(tzinfo=timezone.utc).timestamp())

    # Get current month data
    today = date.today()
    first_day = today.replace(day=1)
    
    energy_data = {
        "stationId": 61553118,
        "startTimestamp": to_ts(first_day.strftime('%Y-%m-%d')),
        "endTimestamp": to_ts(today.strftime('%Y-%m-%d')),
    }

    print("\n=== Fetching Energy Data ===")
    resp_energy = requests.post(url_energy, headers=headers, json=energy_data)
    
    current_month_production = 0
    overall_production = 0
    
    if resp_energy.status_code == 200:
        try:
            energy_json = resp_energy.json()
            # Adjust keys based on actual API response
            current_month_production = energy_json.get('power', {}).get('currentMonth', 0) or 0
            overall_production = energy_json.get('power', {}).get('cumulative', 0) or 0
            print(f"Current Month Production: {current_month_production} kWh")
            print(f"Overall Production: {overall_production} kWh")
        except Exception as e:
            print(f"Error parsing energy data: {e}")
    else:
        print(f"Error fetching energy data: {resp_energy.status_code}")

    # ========================
    # Calculate Savings
    # ========================
    RATE_PER_KWH = 11.15  # PHP per kWh
    current_month_savings = current_month_production * RATE_PER_KWH
    overall_savings = overall_production * RATE_PER_KWH

    print(f"Current Month Savings: PHP {current_month_savings:,.2f}")
    print(f"Overall Savings: PHP {overall_savings:,.2f}")

    # ========================
    # Create Campaign with Savings
    # ========================
    html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2ecc71; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                .savings-box {{ background-color: #ecf0f1; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .savings-item {{ margin: 15px 0; font-size: 16px; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #2ecc71; }}
                .label {{ color: #7f8c8d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>☀️ Your Solar Energy Savings Report</h1>
                </div>
                
                <p>Hello,</p>
                <p>Great news! Your solar installation is generating amazing savings. Here's your latest energy report:</p>
                
                <div class="savings-box">
                    <div class="savings-item">
                        <div class="label">Current Month Production</div>
                        <div>{current_month_production:,.2f} kWh</div>
                    </div>
                    
                    <div class="savings-item">
                        <div class="label">Current Month Savings (kWh × PHP 11.15)</div>
                        <div class="amount">PHP {current_month_savings:,.2f}</div>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #bdc3c7; margin: 20px 0;">
                    
                    <div class="savings-item">
                        <div class="label">Overall Production (Since Installation)</div>
                        <div>{overall_production:,.2f} kWh</div>
                    </div>
                    
                    <div class="savings-item">
                        <div class="label">Overall Savings (Since Installation)</div>
                        <div class="amount">PHP {overall_savings:,.2f}</div>
                    </div>
                </div>
                
                <p>Keep harnessing the power of the sun! 🌞</p>
                <p>Best regards,<br><strong>Writeshop Solar Team</strong></p>
            </div>
        </body>
        </html>
    """

    email_campaign = sib_api_v3_sdk.CreateEmailCampaign(
        name="Solar Savings Report - " + today.strftime('%B %Y'),
        subject=f"Your Solar Savings This Month: PHP {current_month_savings:,.2f}",
        sender={
            "name": "Writeshop Solar",
            "email": "hello@marketing.writeshopsolar.com"
        },
        html_content=html_content,
        recipients={"listIds": [2, 7]},
        scheduled_at="2025-11-17 13:29:01"
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
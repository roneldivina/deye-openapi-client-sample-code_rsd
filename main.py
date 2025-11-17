"""
Master script: combines all clientcode modules into one file
"""

import requests
from pprint import pprint
from datetime import datetime, timezone
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
    """Create and send email campaign via Brevo"""
    API_KEY = "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"

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = API_KEY

    api_instance = sib_api_v3_sdk.EmailCampaignsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email_campaign = sib_api_v3_sdk.CreateEmailCampaign(
        name="Campaign sent via the API",
        subject="My subject",
        sender={
            "name": "Writeshop Solar",
            "email": "hello@marketing.writeshopsolar.com"
        },
        html_content="""
            <html><body>
            <h1>Congratulations!</h1>
            <p>This campaign was sent using the Brevo API.</p>
            </body></html>
        """,
        recipients={"listIds": [2, 7]},
        scheduled_at="2025-11-17 20:10:01"
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
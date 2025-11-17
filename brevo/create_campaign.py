# ------------------
# Create a campaign
# ------------------

from __future__ import print_function
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

# -------------------------
# Configure Brevo API
# -------------------------

API_KEY = "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"

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = API_KEY

api_instance = sib_api_v3_sdk.EmailCampaignsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)

# -------------------------
# Define the email campaign
# -------------------------

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

    scheduled_at="2025-11-17 00:00:01"
)

# -------------------------
# Send campaign
# -------------------------

try:
    api_response = api_instance.create_email_campaign(email_campaign)
    pprint(api_response)
except ApiException as e:
    print("Error calling EmailCampaignsApi->create_email_campaign: %s\n" % e)

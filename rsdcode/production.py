import requests
from clientcode import variable
from pprint import pprint

if __name__ == '__main__':
    url = variable.baseurl + '/device/history'
    headers = variable.headers

    data = {
        "deviceSn": "2505240025",
        # "granularity": 3,
        # "startAt": "2025-09",
        # "endAt": "2025-10",
        "granularity": 4,
        "startAt": "2025",
        "endAt": "2025",
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    pprint(result)

    # Extract 'Production' value and calculate savings
    try:
        item_list = result['dataList'][0]['itemList']
        production = next(item for item in item_list if item['name'] == 'Production')
        production_value = float(production['value'])
        savings = production_value * 11.15
        print(f"Savings: ₱{savings:,.2f}")
    except Exception as e:
        print("Could not calculate savings:", e)
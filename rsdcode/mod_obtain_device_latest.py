import requests
from clientcode import variable

if __name__ == '__main__':
    url = variable.baseurl + '/device/latest'
    headers = variable.headers

    data = {
        "deviceList": [
            "2505240025"    # Replace with your deviceSn
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    result = response.json()
    print(result)

    # Extract monthly and total solar production
    try:
        device_data = result['data'][0]  # Adjust if your response structure is different
        month_production = device_data.get('monthPower', 'N/A')
        total_production = device_data.get('totalPower', 'N/A')
        print(f"Monthly Solar Production: {month_production} kWh")
        print(f"Total Solar Production: {total_production} kWh")
    except (KeyError, IndexError):
        print("Could not extract monthly or total production from response.")
import requests
from clientcode import variable
from pprint import pprint

if __name__ == '__main__':
    url = variable.baseurl + '/station/latest'
    headers = variable.headers
    data = {
        "stationId": 61553118         # Replace with your stationId in deyecloud
    }

    response = requests.post(url, headers=headers, json=data)

    # print(response.status_code)
    pprint(response.status_code)
    # print(response.json())
    pprint(response.json())
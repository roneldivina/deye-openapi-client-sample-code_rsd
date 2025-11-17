import requests
from clientcode import variable
from pprint import pprint
from datetime import datetime, timezone

# ...existing code...
if __name__ == '__main__':
    # url = variable.baseurl + '/station/list'
    url = variable.baseurl + '/station/alertList'
    # copy headers and ensure content-type
    headers = dict(variable.headers) if hasattr(variable, 'headers') else {}
    headers.setdefault('Content-Type', 'application/json')

    def to_ts(date_str, fmt='%Y-%m-%d'):
        dt = datetime.strptime(date_str, fmt)
        return int(dt.replace(tzinfo=timezone.utc).timestamp())

    # use Unix timestamps (seconds) and pagination per docs
    data = {
        "stationId": 61553118,
        "startTimestamp": to_ts("2025-10-18"),
        "endTimestamp": to_ts("2025-12-30"),
        "page": 1, # page number
        "size": 1  # number of records per page
    }

    print("Request payload:")
    pprint(data)

    response = requests.post(url, headers=headers, json=data)

#     pprint(response.status_code)
#     try:
#         pprint(response.json())
#     except ValueError:
#         print(response.text)
# # ...existing code...

    pprint(response.status_code)
    try:
            j = response.json()

            # helper to format timestamps
            def format_ts(ts, to_local=False):
                if ts is None:
                    return None
                ts = int(ts)
                if to_local:
                    # local time (system timezone)
                    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # UTC time
                    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

            # Convert alertStartTime / alertEndTime if present
            items = j.get('stationAlertItems')
            if items:
                for it in items:
                    it['alertStartTime_hr_utc'] = format_ts(it.get('alertStartTime'), to_local=False)
                    it['alertEndTime_hr_utc'] = format_ts(it.get('alertEndTime'), to_local=False)
                    it['alertStartTime_hr_local'] = format_ts(it.get('alertStartTime'), to_local=True)
                    it['alertEndTime_hr_local'] = format_ts(it.get('alertEndTime'), to_local=True)

            pprint(j)
    except ValueError:
            print(response.text)
# ...existing code...
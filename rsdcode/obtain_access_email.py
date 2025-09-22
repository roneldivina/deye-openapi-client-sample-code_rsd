
import requests

if __name__ == '__main__':
  url = 'https://eu1-developer.deyecloud.com/v1.0/account/token?appId=202509192392002'
  headers = {
      'Content-Type': 'application/json'
  }
  # Body
  data = {
      "appSecret": "fa11d3c6dc305658c6c44b20c676302c",
      "email": "engrdivina@writeshopsolar.com",  #email of DeyeCloud account
      "password": "pece01@01" #password of DeyeCloud account
  }
  try:
      # Send POST Request 
      response = requests.post(url, headers=headers, json=data)
      response.raise_for_status()  
      # print response status
      print(response.status_code)
      print(response.json())

  except requests.exceptions.HTTPError as err:
      print(f"HTTP error occurred: {err}")
  except Exception as err:
      print(f"Other error occurred: {err}")
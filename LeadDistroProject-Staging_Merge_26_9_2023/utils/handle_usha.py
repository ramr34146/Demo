import json
from requests import request as SEND_REQUEST

class USHA:
    def __init__(self):
        self.donotcall_api_url = "https://leads-dnc-api.ushealthgroup.com/api/DoNotCall/IsDoNotCall?phone={}"

        self.headers  = {
              'accept': 'text/plain',
              'X-API-KEY': '0682DE4F-C76B-402D-B55A-B3BFA9EC54B9'
            }

    def DonotCallAPI(self, number):
        is_call_block = False
        response = SEND_REQUEST("GET", self.donotcall_api_url.format(number), headers=self.headers, timeout=30)
        data = json.loads(response.text)
        # print(data)
        try:
            if data['isDoNotCall']: is_call_block = True
        except:pass
        return is_call_block


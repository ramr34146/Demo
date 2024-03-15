from requests import request as SEND_REQUEST
import json

class API_USHA_BULK:
    def __init__(self):
        self.headers = {
            'X-API-KEY': '0682DE4F-C76B-402D-B55A-B3BFA9EC54B9',
            'Content-Type': 'application/json',
        }
        self.scrub_url = "https://leads-dnc-api.ushealthgroup.com/api/DoNotCall/list/"

    def returnUSHAEmptyData(self, phone_numbers):
        data = {}
        for number in phone_numbers:
            data.update({number:False})
        return data

    def GetNumbersData(self, numbers_list):
        try:
            payload = json.dumps({"phoneNumbers": numbers_list})
            response = SEND_REQUEST("POST", self.scrub_url, headers=self.headers, data=payload)
            results = response.json()
            # print(results)
            results = [{mr['PhoneNumber']: mr['IsDoNotCall']} for mr in results]
            results = dict(map(dict.popitem, results))
            return results
        except:
            results = self.returnUSHAEmptyData(numbers_list)
            return results




from requests import request as SEND_REQUEST
import json


class API_LLR_BULK_1API:
    def __init__(self):
        self.headers = {'Content-Type': 'application/json',}
        self.scrub_url = "https://landlineremover.com/api/ld_bulk_numbers_1apikey/"

    def returnLLREmptyData(self, phone_numbers):
        data = {}
        for number in phone_numbers:
            data.update({number:['','']})
        return data

    def GetNumbersData(self, api_key, numbers_list):
        try:
            payload = json.dumps({"api_key":api_key , "numbers": numbers_list})
            response = SEND_REQUEST("POST", self.scrub_url, headers=self.headers, data=payload)
            results = response.json()
            return results
        except:
            results = self.returnLLREmptyData(numbers_list)
            return results


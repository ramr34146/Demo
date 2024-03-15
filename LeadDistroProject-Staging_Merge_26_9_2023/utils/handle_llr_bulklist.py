from requests import request as SEND_REQUEST
import json
from time import sleep

class API_LLR_BULK_LIST:
    def __init__(self, apikey, numbers_list):
        self.headers = {
                'Content-Type': 'application/json',
                'apikey': apikey,
                'passld': '1'
            }
        self.start_url = "https://landlineremover.com/"
        self.request_api_url = f"{self.start_url}api/bulk-list/"
        self.result_api_url = f"{self.start_url}api/bulk-list/results/?page=1&linetype=all&dnctype=all"

        self.numbers_list = numbers_list

    def returnLLREmptyData(self):
        data = {}
        for number in self.numbers_list:
            data.update({number:['','']})
        return data


    def helping_GetResultID(self): 
        payload = json.dumps({"numbers": self.numbers_list})
        response = SEND_REQUEST("POST", self.request_api_url, headers=self.headers, data=payload)
        # print(response)
        if response.status_code == 200:
            result_id = response.json()['result_id']
        else:
            result_id = None
        return result_id

    def helping_GetResultID_Data(self, result_id):
        payload = json.dumps({"resultid": result_id})
        response = SEND_REQUEST("POST", self.result_api_url, headers=self.headers, data=payload)
        if response.status_code == 200:
            data = response.json()
            try:
                data = data['results']
                return True, data
            except:
                return True, None 
        return False, None


    def BulkList_GetNumbersData(self):
        result_id = self.helping_GetResultID()
        # print(result_id)

        if result_id is None:
            return self.returnLLREmptyData()

        sleep(5) #wait before sending first reqeust to check results. optional but useful

        while True:
            status, datas = self.helping_GetResultID_Data(result_id)
            if status is True:
                if datas is None:
                    # print("checking again")
                    sleep(5)
                    continue
                break
            else:
                return self.returnLLREmptyData()

        result = {}
        for data in datas:
            result.update({data['phonenumber']:[data['line_type'],data['dnc_type']]})
        return result
        

from requests import request as SEND_REQUEST
import json 

class LandlineRemoverAPI:
    def __init__(self, apikeys=[]):
        self.apikeys_fortypedata = apikeys

    def GetAPIStatus(self, api_key):
        api_url = f"https://landlineremover.com/api/check-credits?apikey={api_key.strip()}&check_topup=1"
        data = SEND_REQUEST("GET", api_url).json()
        try:
            if data['status'] == 'success':
                return data
        except:
            pass
        return False

    def GetNumberData(self, number):
        return_data = {"mobile": '', "linetype": '', "dnctype": ''}
        for apikey in self.apikeys_fortypedata:
            api_url = f"https://landlineremover.com/api/check-number?apikey={apikey}&number={number}"
            try:
                response = SEND_REQUEST("GET", api_url, timeout=30)
                data = response.json()
                data = data['data']
                return_data['mobile'] = str(data['Number']).lower()
                return_data['linetype'] = str(data['LineType']).lower()
                return_data['dnctype'] = str(data['DNCType']).lower()
                break
            except :
                continue
        return return_data

    def handleAutoTopUp(self, apikey, total_leads):
        try:
            api_url = "https://landlineremover.com/api/ld_auto_topup/"
            payload = json.dumps({"api_key": apikey, "leads_count": total_leads})
            headers = {'Content-Type': 'application/json'}
            SEND_REQUEST("POST", api_url, headers=headers, data=payload, timeout=30)
        except:
            pass
        return None



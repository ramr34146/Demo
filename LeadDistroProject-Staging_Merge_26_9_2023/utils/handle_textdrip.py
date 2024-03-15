from requests import request as SEND_REQUEST
import json


class TextDrip:
    def __init__(self):
        self.create_contact_url = "https://api.textdrip.com/api/create-contact"
        self.get_campaign_url = "https://api.textdrip.com/api/get-campaign"
        self.get_drip_message_url = "https://api.textdrip.com/api/get-drip-messages"


    def CreateContact(self, auth_token, campaign_id, data, is_usha=False):
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data['campaign'] = [campaign_id]
        if is_usha:
            data['source'] = "USHA"
        payload = json.dumps(data)
        try:
            response = SEND_REQUEST("POST", self.create_contact_url, headers=headers, data=payload)
            #print(response.status_code, response.text)
        except:
            pass
        return 0


    def GetCampaignData(self, auth_token):
        return_data = []
        try:
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            get_response = SEND_REQUEST("POST", self.get_campaign_url, headers=headers)
            for cam in get_response.json()['data']:
                return_data.append(cam)
        except: pass
        return return_data

    def GetCampaignDripMessage(self, auth_token, campaign_id):
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        request_body = {
            'campaign_id': campaign_id
        }
        payload = json.dumps(request_body)
        get_response = SEND_REQUEST("POST", self.get_drip_message_url, headers=headers, data=payload)
        if get_response.status_code == 200:
            response_json = get_response.json()
            campaign_drip_message_status = response_json['status']
            return campaign_drip_message_status
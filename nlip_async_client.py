#
# A simple Async NLIP Client based on HTTPX
#

import httpx
from nlip_sdk.nlip import NLIP_Message

class NlipAsyncClient:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    @classmethod
    def create_from_url(cls, base_url:str):
        return NlipAsyncClient(base_url)

    async def async_send(self, msg:NLIP_Message) -> NLIP_Message:
        response = await self.client.post(self.base_url, json=msg.to_dict(), timeout=120.0, follow_redirects=True)
        data = response.raise_for_status().json()
        nlip_msg = NLIP_Message(**data)
        return nlip_msg
        

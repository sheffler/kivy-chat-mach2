#
# An NLIP client that uses a 401 response to query the user for authenticaiton
#

import httpx
from nlip_sdk.nlip import NLIP_Message

class AuthenticatingNlipAsyncClient:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.recursion = 0

        self.on_login_elicitation = None  # obtain username/password

    # add basic auth to the client and recreate it
    def add_basic_auth(self, username: str, password: str):
        auth = httpx.BasicAuth(username=username, password=password)
        self.client = httpx.AsyncClient(auth=auth)

    # add digest auth to the client and recreate it
    def add_digest_auth(self, username: str, password: str):
        auth = httpx.DigestAuth(username=username, password=password)
        self.client = httpx.AsyncClient(auth=auth)

    # register an elicitation for username/password
    def on_login_requested(self, on_login_elicitation):
        print(f"ON LOGIN REQUESTED")
        self.on_login_elicitation = on_login_elicitation

    # call the elicitation and get the credentials
    async def elicit_login_credentials(self):
        print(f"ELICIT LOGIN CREDENTIALS")
        if self.on_login_elicitation:
            (username, password) = await self.on_login_elicitation(self)
            return (username, password)
        else:
            print(f"NO LOGIN HANDLER REGISTERED")
            return ("", "")

    @classmethod
    def create_from_url(cls, base_url:str):
        return AuthenticatingNlipAsyncClient(base_url)

    async def Xasync_send(self, msg:NLIP_Message) -> NLIP_Message:
        response = await self.client.post(self.base_url, json=msg.to_dict(), timeout=120.0, follow_redirects=True)
        data = response.raise_for_status().json()
        nlip_msg = NLIP_Message(**data)
        return nlip_msg

    async def async_send(self, msg:NLIP_Message) -> NLIP_Message:
        self.recursion = 0
        return await self._async_send(msg)
        
    async def _async_send(self, msg:NLIP_Message) -> NLIP_Message:
        print(f"ASYNC_SEND")
        try:
            response = await self.client.post(self.base_url, json=msg.to_dict(), timeout=120.0, follow_redirects=True)
            response.raise_for_status() # raise an exception if status
            data = response.json()
            nlip_msg = NLIP_Message(**data)
            return nlip_msg

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print(f"401 Headers:{e.response.headers}")
                self.recursion += 1
                if self.recursion > 4:
                    raise Exception(f"Too many login tries:{self.recursion}")
                else:
                    if e.response.headers.get('www-authenticate', None) is not None:
                        scheme = e.response.headers.get('www-authenticate')
                        print(f"Authentication Required:{scheme}.  Requesting Credentials")
                        if scheme == 'Basic':
                            future = self.elicit_login_credentials()
                            (username, password) = await future
                            self.add_basic_auth(username, password)
                        elif scheme.startswith('Digest'):
                            future = self.elicit_login_credentials()
                            (username, password) = await future
                            self.add_digest_auth(username, password)
                        else:
                            raise Exception(f"Unrecognized header: www-authenticate:{scheme}")

                        # send the message again with the authorization
                        return await self._async_send(msg)
                    else:
                        raise e

            else:
                raise e
        

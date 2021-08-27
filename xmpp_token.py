import asyncio
import json
import random
import string
import os
from aiohttp import ClientSession
from Crypto.Hash import keccak
from typing import Optional

# GET THE DOMAIN FROM https://github.com/Mixaill/galaxy-integration-wargaming/blob/master/wgc/wgc_constants.py
# WGCRealms, domain_wgnet, client_id

DOMAIN = "https://asia.wargaming.net"

URL_CHALLENGE = f"{DOMAIN}/id/api/v2/account/credentials/create/oauth/token/challenge/"
URL_OAUTH_TOKEN = f"{DOMAIN}/id/api/v2/account/credentials/create/oauth/token/"
URL_TOKEN1 = f"{DOMAIN}/id/api/v2/account/credentials/create/token1/"

HTTP_USER_AGENT = 'wgc/20.01.00.9514'
CLIENT_ID = "Xe2oDM8Z6A4N70VZIV8RyVLHpvdtVPYNRIIYBklJ"  # CHECK COMMENT ON TOP
TRACKING_ID = os.getenv('TRACKING_ID')
USERNAME = os.getenv('WOWS_USERNAME')
PASSWORD = os.getenv('WOWS_PASSWORD')


class XmppToken:
    def __init__(self, username: str, password: str):
        self._username = username,
        self._password = password
        self._session: Optional[ClientSession] = None

    async def _get_challenge(self):
        try:
            async with self._session.get(URL_CHALLENGE) as response:
                return json.loads(await response.content.read())
        except Exception:
            return None

    @staticmethod
    async def _calculate_challenge(challenge: dict):
        prefix = '0' * challenge['complexity']
        c_version = challenge['algorithm']['version']
        c_complexity = challenge['complexity']
        c_ts = challenge['timestamp']
        c_resource = challenge['algorithm']['resourse']  # yep, "resourse".
        c_extension = challenge['algorithm']['extension']
        c_random_str = challenge['random_string']
        hashcash = f"{c_version}:{c_complexity}:{c_ts}:{c_resource}:{c_extension}:{c_random_str}:".encode('utf8')

        pow_number = 0
        while True:
            keccak_hash = keccak.new(digest_bits=512)
            keccak_hash.update(hashcash + str(pow_number).encode('utf-8'))

            if keccak_hash.hexdigest().startswith(prefix):
                return pow_number

            pow_number = pow_number + 1

    async def _login(self, power: int) -> str:
        post_data = {
            "username": self._username,
            "password": self._password,
            "grant_type": "urn:wargaming:params:oauth:grant-type:basic",
            "client_id": CLIENT_ID,
            "exchange_code": ''.join(random.choices(string.digits + 'ABCDEF', k=32)),
            "tid": TRACKING_ID,
            "pow": power
        }

        async with self._session.post(URL_OAUTH_TOKEN, data=post_data) as response:
            if response.status == 202:
                return await self._wait_login(response.headers['Location'])
            elif response.read() == 200:
                return json.loads(await response.content.read())['access_token']

    async def _wait_login(self, location: str) -> str:
        try:
            while True:
                async with self._session.get(location) as response:
                    if response.status == 200:
                        return json.loads(await response.content.read())['access_token']
                await asyncio.sleep(0.5)
        except Exception:
            return ""

    async def _acquire_token1(self, login_token: str) -> int:
        post_data = {
            'requested_for': 'xmppcs',
            'access_token': login_token
        }
        async with self._session.post(URL_TOKEN1, data=post_data) as response:
            if response.status == 202:
                return await self._wait_token1(response.headers['Location'])
            elif response.status == 200:
                return json.loads(await response.content.read())['token']

    async def _wait_token1(self, location: str) -> int:
        try:
            while True:
                async with self._session.get(location) as response:
                    if response.status == 200:
                        return json.loads(await response.content.read())['token']
                await asyncio.sleep(0.5)
        except Exception:
            return -1

    async def main(self):
        self._session = ClientSession()
        self._session.headers.update({"User-Agent": HTTP_USER_AGENT})

        if challenge := await self._get_challenge():
            power = await self._calculate_challenge(challenge['pow'])
            token = await self._login(power)
            print(await self._acquire_token1(token))
        await self._session.close()

    def start(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main())


if __name__ == '__main__':
    t = XmppToken(USERNAME, PASSWORD)
    t.start()

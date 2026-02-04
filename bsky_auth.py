import sys
import urllib3
import json

from bsky_api_handler import BskyApiHandler
from config import Config

# BskyAccount handles authentication and posting to Bluesky
class BskyAccount():
    def __init__(self, config: Config, bsky_api_handler: BskyApiHandler):
        cfg = config
        self.bsky_api_handler = bsky_api_handler

        self.handle = cfg.config['bsky_handle']
        self.password = cfg.config['bsky_password']
        self.did = self.__get_did()
        self.apiKey = self.__get_api_key()

    def __get_did(self):
        http = urllib3.PoolManager()
        DID_URL = "https://bsky.social/xrpc/com.atproto.identity.resolveHandle"
        did_resolve = http.request("GET", DID_URL, fields={"handle": self.handle})

        if 'error' in json.loads(did_resolve.data):
            print(json.loads(did_resolve.data))
            sys.exit()
        else:
            return json.loads(did_resolve.data)["did"]

    def __get_api_key(self):
        http = urllib3.PoolManager()
        API_KEY_URL = "https://bsky.social/xrpc/com.atproto.server.createSession"

        post_data = {
            "identifier": self.did,
            "password": self.password
        }

        headers = {
            "Content-Type": "application/json"
        }

        api_key_response = http.request("POST", API_KEY_URL, headers=headers, body=json.dumps(post_data))

        return json.loads(api_key_response.data)["accessJwt"]

    def post_article(self, article):
        self.bsky_api_handler.create_post(self.bsky_api_handler.structure_post_from_article(self.handle, self.password, article))
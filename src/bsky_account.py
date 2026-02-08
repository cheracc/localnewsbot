from __future__ import annotations
import sys
from typing import Any, Dict
import requests
import urllib3
import json

from .bsky_post_handler import BskyPostHandler
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config
    from src.bsky_post import BskyPost

# BskyAccount handles authentication and posting to Bluesky
class BskyAccount():
    
    def __init__(self, config: Config):
        self.config = config
        self.bsky_post_handler = BskyPostHandler(self.config)
        self.pds_url = self.config.get_pds_url()
        self.handle = self.config.handle
        self.password = self.config.password
        self.did = self.__get_did()
        self.apiKey = self.__get_api_key()
        self.session = {}

    def post_article(self, article: BskyPost) -> None:
        self.bsky_post_handler.create_post_new(article)

    def get_session_string(self) -> str:
        return self.get_session()["accessJwt"]

    def get_session(self) -> Dict[str, Any]:
        # First check if we already have a session token
        if self.session and self.session["refreshJwt"]:
            # We do, refresh it first then return it
            self.__refresh_session()
            return self.session
        
        # Didn't have a session, so try to load it from config
        self.session = self.config.get_saved_session()
        if self.session:
            # found one in config, try to refresh it - if it's old or invalid, this will use handle/password instead
            self.__refresh_session()
        else:
            # there was no session saved anywhere, so use handle/password
            self.__login_with_handle_password()
        return self.session

    def __get_did(self) -> str:
        http = urllib3.PoolManager()
        DID_URL = "https://bsky.social/xrpc/com.atproto.identity.resolveHandle"
        did_resolve = http.request("GET", DID_URL, fields={"handle": self.handle})

        if 'error' in json.loads(did_resolve.data):
            print(json.loads(did_resolve.data))
            sys.exit()
        else:
            return json.loads(did_resolve.data)["did"]

    def __get_api_key(self) -> str:
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

    def __login_with_handle_password(self) -> None:
        resp = requests.post(
            self.pds_url + "/xrpc/com.atproto.server.createSession",
            json={"identifier": self.handle, "password": self.password},
        )
        resp.raise_for_status()
        self.session = resp.json()
    
    def __refresh_session(self) -> None:
        if not self.session or not self.session["refreshJwt"]:
            self.config.logger.warning("bsky_account.bsky_refresh_session(): No session to refresh. Using handle/password instead")
            self.__login_with_handle_password()
            return

        resp = requests.post(
            self.pds_url + "/xrpc/com.atproto.server.refreshSession",
            headers={"Authorization": "Bearer " + self.session["refreshJwt"]},
        )
        try:
            resp.raise_for_status()
        except Exception as e:
            self.config.logger.warning(f"bsky_account.bsky_refresh_session(): Error refreshing session: {e}. Using handle/password instead")
            self.__login_with_handle_password()
            return

        self.session = resp.json()
        if self.session["accessJwt"] and self.session["refreshJwt"]:
            self.config.logger.debug("Successfully refreshed bsky session token")
            self.config.save_session()
            return
        
        else:
            self.config.logger.warning(f"bsky_account.bsky_refresh_session(): Error refreshing session: {self.session}")
            self.__login_with_handle_password()
            return


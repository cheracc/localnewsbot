from __future__ import annotations
import sys
from typing import Any, Dict
from atproto import Client
from atproto.exceptions import AtProtocolError
import requests
import urllib3
import json

from .bsky_chat_handler import BskyChatHandler
from .bsky_post_handler import BskyPostHandler
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config
    from src.bsky_post import BskyPost

# BskyAccount handles authentication and posting to Bluesky
class BskyAccount():
    
    def __init__(self, config: Config):
        self.__chat_handler = None
        self.__post_handler = None
        self.config = config
        self.client = Client()
        self.pds_url = self.config.get_pds_url()
        self.handle = self.config.handle
        self.password = self.config.password
        self.__did = None
        self.session_string = self.config.get_saved_session()

    def login(self) -> None:
        if self.session_string:
            self.config.logger.debug("Using existing session string to authenticate")
            try:
                self.client.login(session_string=self.session_string)
                return
            except AtProtocolError as e:
                self.config.logger.warning(f"Session string login failed: {e}. Attempting password login.")
                # If session string login fails, fall back to password login

        user, paswd = self.config.get_handle_password()
        try:
            self.client.login(user, paswd)
            self.config.logger.debug(f"Logged in {user} (session: {self.client.export_session_string()})")
            self.session_string = self.client.export_session_string()
        except AtProtocolError as e:
            self.config.logger.error(f"Could not login user {user}: {e}")
            raise

    def get_post_handler(self) -> BskyPostHandler:
        if not self.__post_handler:
            self.__post_handler = BskyPostHandler(self.config)
        return self.__post_handler

    def get_chat_handler(self) -> BskyChatHandler:
        if not self.__chat_handler:
            self.__chat_handler = BskyChatHandler(self.config)
        return self.__chat_handler

    def post_article(self, article: BskyPost) -> None:
        self.get_post_handler().create_post_new(article)

    def get_did(self) -> str:
        if not self.__did:
            try:
                self.__did = self.client.resolve_handle(self.handle).did
                self.config.logger.debug(f"Resolved DID for {self.handle}: {self.__did}")
            except AtProtocolError as e:
                self.config.logger.error(f"Error fetching DID for {self.handle}: {e}")
                raise
        return self.__did
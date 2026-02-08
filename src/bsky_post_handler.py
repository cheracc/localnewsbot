"""
now uses atproto sdk
"""
from __future__ import annotations
import re
import requests

from atproto.exceptions import AtProtocolError
from atproto_client import models
from typing import TYPE_CHECKING
from src.bsky_post import BskyPost
if TYPE_CHECKING:
    from src.config import Config

class BskyPostHandler:
    def __init__(self, config: Config):
        self.config = config
        self.client = config.get_bsky_account().client
        self.logger = config.logger

    def parse_hashtags_new(self, post_text: str) -> list[models.AppBskyRichtextFacet.Main]:
        facets =[]
        hashtag_regex = rb"[$|\W](#([a-zA-Z0-9_]{1,30}))"
        text_bytes = post_text.encode("UTF-8")
        
        for m in re.finditer(hashtag_regex, text_bytes):
            start = m.start(1)
            end = m.end(1)
            tag = m.group(1).decode("UTF-8")
            self.logger.debug(f"found hashtag: {tag} at bytes {start} to {end}")
            facets.append(models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Tag(tag = tag)],
                index = models.AppBskyRichtextFacet.ByteSlice(byte_start=start, byte_end=end)
            ))
        return facets

    def parse_mentions_new(self, post_text: str) -> list[models.AppBskyRichtextFacet.Main]:
        facets = []
        mention_regex = rb"[$|\W](@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
        text_bytes = post_text.encode("UTF-8")
        
        for m in re.finditer(mention_regex, text_bytes):
            start = m.start(1)
            end = m.end(1)
            handle = m.group(1)[1:].decode("UTF-8")
            did = self.client.resolve_handle(handle).did
            facets.append(models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Mention(did=did)],
                index = models.AppBskyRichtextFacet.ByteSlice(byte_start=start, byte_end=end)
            ))
        return facets

    def parse_urls_new(self, post_text: str) -> list[models.AppBskyRichtextFacet.Main]:
        facets = []
        url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
        text_bytes = post_text.encode("UTF-8")
        
        for m in re.finditer(url_regex, text_bytes):
            start = m.start(1)
            end = m.end(1)
            url = m.group(1).decode("UTF-8")
            facets.append(models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Link(uri = url)],
                index = models.AppBskyRichtextFacet.ByteSlice(byte_start = start, byte_end = end)
            ))

        return facets

    def parse_facets_new(self, post_text: str) -> list[models.AppBskyRichtextFacet.Main]:
        facets = self.parse_urls_new(post_text)
        facets.extend(self.parse_mentions_new(post_text))
        facets.extend(self.parse_hashtags_new(post_text))
        return facets

    def get_embed_card(self, bsky_post: BskyPost) -> models.AppBskyEmbedExternal.Main:
        card= models.AppBskyEmbedExternal.External(
            uri = bsky_post.link,
            title = bsky_post.headline,
            description = bsky_post.description,
        )
        img_url = bsky_post.img_url

        if img_url and len(img_url) > 0:
            try:
                self.logger.debug(f"Attempting to get imageblob for {img_url}")
                resp = requests.get(img_url)
                resp.raise_for_status()
                self.config.get_bsky_account().login()
                card.thumb = self.client.upload_blob(resp.content).blob
            except Exception as e:
                self.logger.warning(f"Could not fetch image for embed card: {bsky_post.img_url},{e}")
                card.thumb = None

        return models.AppBskyEmbedExternal.Main(external = card)

    def create_post_new(self, bsky_post: BskyPost) -> bool:
        text = bsky_post.get_post_text()
        profile_identity = self.config.get_bsky_account().handle
        embed = self.get_embed_card(bsky_post)
        facets = self.parse_facets_new(text)
    
        try:
            self.config.get_bsky_account().login()
            response = self.client.send_post(text = text,
                                            profile_identify = profile_identity,
                                            embed = embed,
                                            facets = facets)
            if not response or not response.uri:
                self.logger.warning(f"Could not post article (invalid response): {bsky_post.headline}")
                return False
            return True
        except AtProtocolError as e:
                self.logger.error(f"Error creating post: {e}")
                raise


# Definition of BskyPost class - represents an article to be posted
from __future__ import annotations
import html
import re
import src.tags as tags
from src.aisummary import Summarizer
from typing import Any, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config


class BskyPost:
    def __init__(self, source_name: str, headline: str, description: str, link: str, img_url: str, tag: str, created_at: str, config: Config):
        self.source_name = source_name
        self.headline = headline
        self.description = description
        self.link = link
        self.img_url = img_url
        self.tag = tag
        self.created_at = created_at
        self.post_text = None
        self.config = config

    # gets the text of the post as it will be seen on Bluesky, including tags
    def get_post_text(self) -> str: 
        if not self.post_text:
            self.post_text = self.get_ai_summary()
        if not self.post_text:
            self.post_text = self.format_post_text()
        return self.post_text

    def add_tags_to_post(self) -> str:
        return tags.add_tags_to_post(self, self.config.get_tags())

    def post_to_bluesky(self) -> None: 
        self.post_text = self.get_post_text()
        self.post_text = self.add_tags_to_post()
        self.config.get_bsky_account().post_article(self)

    def format_post_text(self) -> str:
        text = f"{self.headline}\n\n{self.description}"

        # convert HTML entities
        text = html.unescape(text)

        # handle <a href="...">text</a> => "text (url)"
        def _replace_a(m):
            href = m.group(1)
            inner = re.sub(r'<[^>]+>', '', m.group(2) or '')
            return f"{inner} ({href})"
        text = re.sub(r'(?i)<\s*a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</\s*a\s*>', _replace_a, text)

        # replace block-level tags with newlines
        text = re.sub(r'(?i)<\s*(br|p|div|li|tr|h[1-6])\b[^>]*>', '\n', text)
        text = re.sub(r'(?i)</\s*(p|div|li|tr|h[1-6])\s*>', '', text)

        # remove any other tags
        text = re.sub(r'<[^>]+>', '', text)

        # normalize whitespace and newlines
        text = text.replace('\r', '')
        text = re.sub(r'\n{3,}', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text).strip()

        return text
    
    def get_post_args(self) -> dict[str, str]:
        return {
            "pds_url": "https://bsky.social",
            "handle": self.config.get_bsky_account().handle,
            "password": self.config.get_bsky_account().password,
            "embed_url": self.link,
            "text": self.post_text if self.post_text else self.format_post_text(),
        }
    
    def get_ai_summary(self) -> str:

        return self.config.get_summarizer().summarize(self.link)
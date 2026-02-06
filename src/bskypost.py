# Definition of BskyPost class - represents an article to be posted
import html
import re
from src.aisummary import Summarizer
import src.tags as tags


class BskyPost:
    def __init__(self, source_name, headline, description, link, img_url, tag, created_at):
        self.source_name = source_name
        self.headline = headline
        self.description = description
        self.formatted_text = None
        self.link = link
        self.img_url = img_url
        self.tag = tag
        self.created_at = created_at
        self.post_text = None

    

    def get_post_text(self, bsky_account):
        if self.formatted_text is None:
#            self.formatted_text = self.format_post_text(tags_config)
            self.formatted_text = self.get_ai_summary(bsky_account)
            if not self.formatted_text:
                self.formatted_text = self.format_post_text(bsky_account.cfg.get_tags())
        return self.add_tags_to_post(bsky_account.cfg.get_tags())

    def add_tags_to_post(self, tags_config):
        return tags.add_tags_to_post(self, tags_config)

    def post_to_bluesky(self, bsky_account):
        self.post_text = self.get_post_text(bsky_account)
        bsky_account.post_article(self)

    def format_post_text(self, tags_config) -> str:
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
    
    def get_post_args(self, bsky_account) -> dict:
        return {
            "pds_url": "https://bsky.social",
            "handle": bsky_account.cfg.handle,
            "password": bsky_account.cfg.password,
            "embed_url": self.link,
            "text": self.post_text
        }
    
    def get_ai_summary(self, bsky_account) -> str:
        ai = Summarizer(bsky_account.cfg)
        return ai.summarize(self.link)
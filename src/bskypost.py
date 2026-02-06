# postablearticle.py
# Definition of BskyPost class - represents an article to be posted
import html
import re
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

    def get_post_text(self, tags_config):
        if self.formatted_text is None:
            self.formatted_text = self.format_post_text(tags_config)
        return self.add_tags_to_post(tags_config)

    def add_tags_to_post(self, tags_config):
        return tags.add_tags_to_post(self, tags_config)

    def post_to_bluesky(self, bsky_account):
        post_text = self.get_post_text(bsky_account.cfg.get_tags_config())
        bsky_account.post_article(post_text)

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
        text = re.sub(r'(?i)</\s*(p|div|li|tr|h[1-6])\s*>', '\n', text)

        # remove any other tags
        text = re.sub(r'<[^>]+>', '', text)

        # normalize whitespace and newlines
        text = text.replace('\r', '')
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text).strip()

        return text
    
    def get_post_args(self, config) -> dict:
        return {
            "pds_url": "https://bsky.social",
            "handle": config.handle,
            "password": config.password,
            "embed_url": self.link,
            "text": self.get_post_text(config.get_tags())
        }
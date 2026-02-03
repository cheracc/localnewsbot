import feedparser

from postablearticle import PostableArticle

# RSS_Source handles parsing news articles from RSS feeds
class RSS_Source():
    def __init__(self, name: str, url: str, tag: str):
        self._name = name
        self._url = url
        self._tag = tag

    def get_articles(self) -> list[PostableArticle]:
        return self.parse_rss()

    def parse_rss(self) -> list[PostableArticle]:
        feed = feedparser.parse(self._url)
        articles = []
        for entry in feed.entries:
            article = PostableArticle(
                source_name=self._name,
                headline=entry.title,
                description=entry.description,
                link=entry.link,
                created_at=entry.published
            )
            articles.append(article)
        return articles
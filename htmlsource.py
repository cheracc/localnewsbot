import newspaper
from config import Config
from postablearticle import PostableArticle
import htmlsource
from newspaper import Article

# WebNewsSource handles parsing news articles from HTML sources using the newspaper3k library
class WebNewsSource:
    def __init__(self, name: str, url: str, tag: str):
        self._name = name
        self._url = url
        self._tag = tag

    def get_articles(self) -> list[PostableArticle]:
        return self.parse_website()

    def parse_website(self) -> list[PostableArticle]:
        news_site = newspaper.build(self._url, memorize_articles=True)
        articles = []
        for art in news_site.articles[:10]:  # Limit to first 10 articles for performance
            try:
                article = htmlsource.Article(art.url)
                article.download()
                article.parse()
            except Exception as e:
                print(f"Error processing article: {e}")
                continue

            extracted_article = PostableArticle(
                source_name=self._name,
                headline=article.title,
                description=article.meta_description or article.text[:200] + '...',
                link=article.url,
                created_at=article.publish_date.strftime('%a, %d %b %Y %H:%M:%S %z') if article.publish_date else ''
            )
            articles.append(extracted_article)
        return articles

# Parse HTML sources from config and return list of PostableArticle
def get_html_sources(config: Config) -> list[PostableArticle]:
	sources = []
	html_sources = config.get_html_sources()
	for _, source_info in html_sources.items():
		sources.append(WebNewsSource(source_info["name"], source_info["url"], source_info["tag"]))

	articles = []

	for source in sources:
		source_articles = source.get_articles()

		# keep only the first x articles
		if source_articles:
			source_articles = source_articles[:config.max_articles_per_feed]

		articles.extend(source_articles)
		print(f"Fetched {len(source_articles)} articles from HTML source: {source._name}")

	return articles

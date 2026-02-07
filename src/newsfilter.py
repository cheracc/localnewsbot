from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bsky_post import BskyPost
    from src.config import Config

# NewsFilter applies filtering rules to a list of PostableArticle objects, the last step before posting to Bluesky
class NewsFilter:
    def __init__(self, config: Config):
        self.data = config.db
        self.config = config
        self.logger = config.get_logger()

    def filter(self, articles: list[BskyPost]) -> list[BskyPost]:
        self.filteredwords = self.config.get_bad_words()
        goodwords = self.config.get_good_words()
        previously_posted = []

        for art in articles:
            if self.data.has_posted_article(art.link):
                previously_posted.append(art)


        previously_excluded = []
        for art in articles:
            if self.data.is_excluded(art.link):
                previously_excluded.append(art)

        to_remove = previously_excluded + previously_posted
        working_articles = [art for art in articles if art not in to_remove]
        
        self.logger.info(f"removed {len(previously_posted)} articles that were already posted and {len(previously_excluded)} articles that were previously excluded")
        
        # Apply headline, body, and URL filters, splitting them into filtered and removed articles
        # apply filters in sequence and accumulate removed articles without duplicating filtered lists
        removed_articles = []
        super_removed_articles = []

        for filter_fn in (self.filter_body, self.filter_url, self.filter_headlines):
            keep, toss = filter_fn(working_articles)
            removed_articles.extend(toss)
            working_articles = keep  # continue filtering only the kept articles
        
        # Apply any custom filters defined in customfilters.py. Create your own filters by making a customfilters.py file
        # and defining a 
        #   filter(articles: list[PostableArticle], logger:logging.Logger) -> tuple[list[PostableArticle], list[PostableArticle]] 
        # function, which returns the filtered articles and the removed articles in that order. (See customfilters.py.example)
        try:
            import src.customfilters
            custom_filtered, custom_removed, super_removed = src.customfilters.filter(working_articles, self.logger)
            working_articles = custom_filtered
            removed_articles.extend(custom_removed)
            super_removed_articles.extend(super_removed)
        except ImportError:
            pass

        for article in removed_articles[:]:
            if any(phrase in article.headline for phrase in goodwords):
                self.logger.info(f"Restoring due to ok phrase match: {article.headline}")
                working_articles.append(article)
                removed_articles.remove(article)

        # put the 'ineligible for restore' articles back in the list so they can be logged to db as 'excluded'
        removed_articles.extend(super_removed_articles)

        for article in removed_articles:
            self.data.record_excluded_article(article.link)
            
        self.logger.debug(f"Added {len(removed_articles)} articles to 'excluded' table in database")

        return working_articles
    
    # Applies headline, body, and URL filters
    def filter_headlines(self, articles: list[BskyPost]) -> tuple[list[BskyPost], list[BskyPost]]: 
        filtered_articles = []
        removed_articles = []
        for article in articles:
            if not any(word in article.headline for word in self.filteredwords):
                filtered_articles.append(article)
            else:
                removed_articles.append(article)
                self.logger.info(f"Excluding due to headline filter: {article.headline}")
        return filtered_articles, removed_articles
    
    def filter_body(self, articles: list[BskyPost]) -> tuple[list[BskyPost], list[BskyPost]]:
        filtered_articles = []
        removed_articles = []
        for article in articles:
            if not any(word in article.description for word in self.filteredwords):
                filtered_articles.append(article)
            else:
                removed_articles.append(article)
                self.logger.info(f"Excluding due to body filter: {article.headline}")
        return filtered_articles, removed_articles
    
    def filter_url(self, articles: list[BskyPost]) -> tuple[list[BskyPost], list[BskyPost]]:
        filtered_articles = []
        removed_articles = []
        for article in articles:
            cleaned_url = article.link.replace("/", " ").replace(".", " ").replace("-", " ")
            self.logger.debug(f"Cleaned URL for filtering: {cleaned_url}")
            if not any(word in cleaned_url for word in self.filteredwords):
                filtered_articles.append(article)
                self.logger.debug(f"URL passed filter: {article.link}")
            else:
                removed_articles.append(article)
                self.logger.info(f"Excluding due to URL filter: {article.headline}")
        return filtered_articles, removed_articles
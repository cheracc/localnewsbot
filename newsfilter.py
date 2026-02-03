import datetime

# NewsFilter applies filtering rules to a list of PostableArticle objects, the last step before posting to Bluesky
class NewsFilter:
    def __init__(self, data, config):
        self.data = data
        self.config = config

    def filter(self, articles):
        self.filteredwords = self.config.get_bad_words()
        goodwords = self.config.get_good_words()
        removed = []

        for art in articles:
            if self.data.has_posted_article(art.link):
                removed.append(art)

        articles = [art for art in articles if art not in removed]

        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] removed {len(removed)} articles that were already posted")

        # Apply headline, body, and URL filters, splitting them into filtered and removed articles
        # apply filters in sequence and accumulate removed articles without duplicating filtered lists
        filtered_articles, removed_articles = self.filter_headlines(articles)
        for filter_fn in (self.filter_body, self.filter_url):
            filtered_articles, removed = filter_fn(filtered_articles)
            removed_articles.extend(removed)


        # Apply any custom filters defined in customfilters.py. Create your own filters by making a customfilters.py file
        # and defining a filter(articles: list[PostableArticle]) -> tuple[list[PostableArticle], list[PostableArticle]] function, 
        # which returns the filtered articles and the removed articles (optionally) in that order.
        try:
            import customfilters
            custom_filtered, custom_removed = customfilters.filter(filtered_articles)
            filtered_articles = custom_filtered
            removed_articles.extend(custom_removed)
        except ImportError:
            pass

        # Move filtered articles to a temp variable so they can be filtered again
        articles = filtered_articles
        filtered_articles = []


        for article in removed_articles[:]:
            if any(phrase in article.headline for phrase in goodwords):
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] Restoring due to ok phrase match: {article.headline}")
                filtered_articles.append(article)
                removed_articles.remove(article)

        return filtered_articles
    
    # Applies headline, body, and URL filters
    def filter_headlines(self, articles):
        filtered_articles = []
        removed_articles = []
        for article in articles:
            if not any(word in article.headline for word in self.filteredwords):
                filtered_articles.append(article)
            else:
                removed_articles.append(article)
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] Excluding due to headline filter: {article.headline}")
        return filtered_articles, removed_articles
    
    def filter_body(self, articles):
        filtered_articles = []
        removed_articles = []
        for article in articles:
            if not any(word in article.description for word in self.filteredwords):
                filtered_articles.append(article)
            else:
                removed_articles.append(article)
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] Excluding due to body filter: {article.headline}")
        return filtered_articles, removed_articles
    
    def filter_url(self, articles):
        filtered_articles = []
        removed_articles = []
        for article in articles:
            if not any(word in article.link for word in self.filteredwords):
                filtered_articles.append(article)
            else:
                removed_articles.append(article)
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] Excluding due to URL filter: {article.headline}")
        return filtered_articles, removed_articles
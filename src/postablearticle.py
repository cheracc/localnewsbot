# postablearticle.py
# Definition of PostableArticle class - represents an article to be posted, accepted by BskyAccount.post_article()
class PostableArticle:
    def __init__(self, source_name, headline, description, link, created_at):
        self.source_name = source_name
        self.headline = headline
        self.description = description
        self.link = link
        self.created_at = created_at


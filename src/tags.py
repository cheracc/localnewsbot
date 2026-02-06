from typing import Dict


def _assign_tags_from_keywords(article, tags_config: Dict[str, list[str]]) -> list[str]:
    assigned_tags = []
    article_text = f"{article.headline} {article.description}".lower()

    for tag, keywords in tags_config.items():
        for keyword in keywords:
            if keyword.lower() in article_text:
                assigned_tags.append(tag)
                break  # No need to check other keywords for this tag

    return assigned_tags

def add_tags_to_post(article, tags_config: Dict[str, list[str]]) -> str:
    tags = _assign_tags_from_keywords(article, tags_config)
    tags.append(article.tag)  # Include the tag of the source
    post_text = article.formatted_text
    if not tags:
        return post_text
    tag_str = " ".join(f"#{tag} " for tag in tags)

    if len(post_text) + len(tag_str) > 300:
        # If adding the tags would exceed the character limit, truncate the post text
        allowed_post_length = 300 - len(tag_str) - 4  # -1 for a newline, -3 for ...
        post_text = post_text[:allowed_post_length].rstrip() + "…"



    return f"{str(post_text).rstrip()}\n{tag_str}"

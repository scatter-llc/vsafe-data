from urllib.parse import quote, urlparse, unquote

status_to_template = {
    0: "inprogress",
    1: "vsn",
    2: "reliable",
    3: "mixed",
    4: "unreliable",
    5: "conspiracy",
    6: "blocked"
}

def to_wikilinks(url_string):
    """
    Converts a string of URLs into a string of MediaWiki-style wiki links

    Args:
        url_string (str): A string containing one or more comma-separated URLs.

    Returns:
        str: A string containing the corresponding Wikipedia wikilinks, separated by commas.
    """
    url_string = url_string.replace(',https://', '\thttps://')
    urls = url_string.split('\t')
    wikilinks = []
    for url in urls:
        url = url.strip()
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path.startswith('/wiki/'):
            title = unquote(path[6:]).replace('_', ' ')
            wikilink = f"[[{title}]]"
            wikilinks.append(wikilink)
    formatted_links = ', '.join(wikilinks)
    return formatted_links

def get_history_link(article_title):
    """
    Generates a Wikipedia article history link for a given article title.

    Args:
        article_title (str): The title of the Wikipedia article.

    Returns:
        str: The URL of the history page for the given article title.
    """
    encoded = quote(article_title)
    return "https://en.wikipedia.org/w/index.php?title=" + encoded + "&action=history"

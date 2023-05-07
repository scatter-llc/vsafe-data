from urllib.parse import urlparse, unquote

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
    encoded = urlparse.quote(article_title)
    return "https://en.wikipedia.org/w/index.php?title=" + encoded + "&action=history"

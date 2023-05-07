from urllib.parse import urlparse, unquote

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

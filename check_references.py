import datetime
import pymysql
import re
import requests
import time
from tld import get_fld
from urllib.parse import quote, urlparse
from credentials import hostname, dbname, username, password

def get_external_links_and_domains(article_url):
    article_title = article_url.replace("https://en.wikipedia.org/wiki/", "").replace("_", " ")
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extlinks",
        "titles": article_title,
        "ellimit": "max"
    }

    while True:
        response = requests.get(api_url, params=params)
        data = response.json()

        for page in data["query"]["pages"].values():
            for extlink in page.get("extlinks", []):
                link = extlink["*"]

                # Remove web.archive.org prefix if present
                archive_prefix = r'^https://web\.archive\.org/web/\d{14}/'
                link = re.sub(archive_prefix, '', link)

                try:
                    domain = get_fld(link, fail_silently=True)
                except Exception:
                    continue

                if not domain:
                    # If domain is an IP address with no TLD
                    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
                    domain_match = ip_pattern.match(link)

                    if domain_match:
                        domain = domain_match.group()

                if domain:
                    yield link, domain

        if "continue" not in data:
            break

        params.update(data["continue"])

def remove_archive_prefix(url, first_level_domain):
    pattern = r'^https://web\.archive\.org/web/(\d{14})/'
    match = re.match(pattern, url)

    if match:
        url = re.sub(pattern, '', url)
        first_level_domain = get_fld(url, fail_silently=True)
        # For IP address-based URLs
        if first_level_domain is None:
            first_level_domain = urlparse(url).hostname
        return url, first_level_domain
    else:
        return url, first_level_domain

def process_wikipedia_urls(article_urls, connection):
    now = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    for article_url in article_urls:
        for url, first_level_domain in get_external_links_and_domains(article_url):
            with connection.cursor() as cursor:
                # Check if the First Level Domain exists in the domains table
                cursor.execute(
                    "SELECT id FROM domains WHERE domain = %s",
                    (first_level_domain,)
                )
                try:
                    domain_id = cursor.fetchone()["id"]
                except:
                    domain_id = None

                if domain_id is None:
                    # If not found, insert the First Level Domain into the domains table
                    cursor.execute(
                        "INSERT INTO domains (domain) VALUES (%s)",
                        (first_level_domain,)
                    )
                    connection.commit()
                    domain_id = cursor.lastrowid

                # Insert a row into the urls table or update it if it already exists
                cursor.execute(
                    "INSERT INTO urls (url, url_appeared_on, domain_id, last_updated) VALUES (%s, %s, %s, %s)"
                    " ON DUPLICATE KEY UPDATE last_updated = VALUES(last_updated)",
                    (url, article_url, domain_id, now)
                )
                connection.commit()


if __name__ == "__main__":
    with open('vsafe-uniq.txt') as f:
        article_urls = [
            f"https://en.wikipedia.org/wiki/{line.strip().replace(' ', '_')}"
            for line in f
        ]

    connection = pymysql.connect(
        host=hostname,
        user=username,
        password=password,
        db=dbname,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        process_wikipedia_urls(article_urls, connection)
    finally:
        connection.close()

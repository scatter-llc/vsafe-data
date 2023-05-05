import requests
import datetime
import pymysql
import re
from tld import get_fld
from urllib.parse import quote, urlparse
from credentials import username, password

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

    base_url = (
        "https://check-references.toolforge.org/v2/statistics/all?"
        "url={url}&regex=test"
    )

    for article_url in article_urls:
        encoded_article_url = quote(article_url, safe='/:')
        request_url = base_url.format(url=encoded_article_url)
        response = requests.get(request_url)

        if response.status_code == 200:
            data = response.json()
            url_details = data.get("url_details", [])

            for entry in url_details:
                url = entry.get("url")
                first_level_domain = entry.get("first_level_domain")
                url, first_level_domain = remove_archive_prefix(url, first_level_domain)

                # Skip the row if any of the columns are missing or empty
                if not first_level_domain or not url or not article_url:
                    continue

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

                    # Check if a row with the specified url and url_appeared_on already exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM urls WHERE url = %s AND url_appeared_on = %s",
                        (url, article_url)
                    )
                    try:
                        count = cursor.fetchone()[0]
                    except:
                        count = 0

                    # Insert a row into the urls table if it doesn't already exist
                    if count == 0:
                        cursor.execute(
                            "INSERT INTO urls (url, url_appeared_on, domain_id, last_updated) VALUES (%s, %s, %s, %s)",
                            (url, article_url, domain_id, now)
                        )
                    else:
                        cursor.execute(
                            "UPDATE urls SET last_updated = %s WHERE url = %s AND url_appeared_on = %s",
                            (now, url, article_url)
                        )


        else:
            print(
                f"Error: Unable to process {article_url}, "
                f"status code: {response.status_code}"
            )

if __name__ == "__main__":
    with open('vsafe-uniq.txt') as f:
        article_urls = [
            f"https://en.wikipedia.org/wiki/{line.strip().replace(' ', '_')}"
            for line in f
        ]

    connection = pymysql.connect(
        host='tools.db.svc.wikimedia.cloud',
        user=username,
        password=password,
        db='s55412__cited_urls_p',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        process_wikipedia_urls(article_urls, connection)
    finally:
        connection.close()

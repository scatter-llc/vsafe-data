import requests
import datetime
import pymysql
from urllib.parse import quote
from credentials import username, password

def process_wikipedia_urls(article_urls, connection):
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
                first_level_domain = entry.get("first_level_domain")
                url = entry.get("url")

                with connection.cursor() as cursor:
                    # Check if the First Level Domain exists in the domains table
                    cursor.execute(
                        "SELECT id FROM domains WHERE domain = %s",
                        (first_level_domain,)
                    )
                    domain_id = cursor.fetchone()["id"]

                    if domain_id is None:
                        # If not found, insert the First Level Domain into the domains table
                        cursor.execute(
                            "INSERT INTO domains (domain) VALUES (%s)",
                            (first_level_domain,)
                        )
                        connection.commit()
                        domain_id = cursor.lastrowid

                    # Insert a row into the urls table
                    cursor.execute(
                        "INSERT INTO urls (url, url_appeared_on, domain_id) VALUES (%s, %s, %s)",
                        (url, article_url, domain_id)
                    )
                    connection.commit()

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

import requests
import csv
import datetime
from urllib.parse import quote

def process_wikipedia_urls(article_urls):
    base_url = (
        "https://check-references.toolforge.org/v2/statistics/all?"
        "url={url}&regex=test"
    )

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    output_filename = f"check-references-{current_date}.csv"

    with open(output_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(
            csvfile, delimiter=',', quotechar='"'
        )
        csv_writer.writerow(['Article URL', 'First Level Domain', 'URL'])

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
                    csv_writer.writerow([article_url, first_level_domain, url])
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
        process_wikipedia_urls(article_urls)

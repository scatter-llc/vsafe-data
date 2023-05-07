import pymysql
import re
import requests
import urllib.parse
from credentials import hostname, dbname, username, password
from utility import *

# Connect to MySQL database
def create_conn():
    try:
        connection = pymysql.connect(user=username,
                                     password=password,
                                     host=hostname,
                                     database=dbname)
        return connection
    except pymysql.Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

# Get the required domain_id and count from the database
def get_domains_and_counts(connection):
    cursor = connection.cursor()
    query = """
        SELECT domains.id, domains.domain, COUNT(urls.domain_id) AS count
        FROM urls
        JOIN domains ON urls.domain_id = domains.id
        WHERE urls.last_updated = (SELECT MAX(last_updated) FROM urls) AND domains.frequent_domain_notification IS NULL
        GROUP BY urls.domain_id
        HAVING COUNT(urls.domain_id) >= 10
        ORDER BY count DESC;
    """

    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

# Format the alerts as per the required format
def create_alerts(domains_and_counts):
    alerts = []

    for i, (domain_id, domain, count) in enumerate(domains_and_counts, 1):
        alert = f"""| type{i}   = frequent-domain
| msg{i}     = '''{domain}''' appears {count} times on articles
| action{i}  = [[Wikipedia:Vaccine safety/Reports#Frequent domain use|view report]]
| time{i}    = ~~~~~"""
        alerts.append(alert)

    return alerts

# Insert the new alerts in the existing wikitext
def insert_alerts(alerts, wikitext):
    start_index = wikitext.index("{{Alert list") + len("{{Alert list")

    for alert in reversed(alerts):
        wikitext = wikitext[:start_index] + "\n" + alert + wikitext[start_index:]

    return wikitext

# Load wikitext from the given URL
def load_wikitext(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error while loading wikitext from URL: {response.status_code}")
        return None

# Renumber notifications and align parameter names, equal signs, and values
def renumber_and_align(wikitext):
    lines = wikitext.split('\n')
    counter = 1

    for i, line in enumerate(lines):
        if re.match(r'\| type\d+ *=', line):
            lines[i] = f"| type{counter}   =" + line.split('=')[1]
            counter += 1

        for param in ['msg', 'action', 'time']:
            if re.match(fr'\| {param}\d+ *=', line):
                lines[i] = f"| {param}{counter - 1}   =" + line.split('=')[1]

    return '\n'.join(lines)

# Update frequent_domain_notification for each domain
def update_frequent_domain_notification(connection, domains_and_counts):
    cursor = connection.cursor()

    for domain_id, domain, count in domains_and_counts:
        query = f"""
            UPDATE domains
            SET frequent_domain_notification = 1
            WHERE id = {domain_id};
        """
        cursor.execute(query)

    connection.commit()
    cursor.close()

# Fetch flagged domains and articles from the database
def get_flagged_domains_and_articles(connection):
    cursor = connection.cursor()
    query = """
        SELECT domains.domain, domains.status, urls.url_appeared_on
        FROM urls
        JOIN domains ON urls.domain_id = domains.id
        WHERE urls.appeared_on_article_notification IS NULL
            AND domains.status IN (3, 4, 5, 6);
    """

    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

# Create alerts for flagged domains
def create_flagged_domain_alerts(flagged_domains_and_articles):
    alerts = []
    print(history_link)
    for i, (domain, status, article) in enumerate(flagged_domains_and_articles, 1):
        article = to_wikilinks(article).replace('[[', '').replace(']]', '')
        history_link = get_history_link(article)
        alert = f"""| type{i}   = flagged-domain
| msg{i}     = '''{domain}''' (marked as {{{{vsrate|{status_to_template[status]}}}}}) appears in '''[[{article}]]'''
| action{i}  = [{history_link} view article history]
| time{i}    = ~~~~~"""
        alerts.append(alert)

    return alerts

def main():
    connection = create_conn()
    if connection:
        domains_and_counts = get_domains_and_counts(connection)
        flagged_domains_and_articles = get_flagged_domains_and_articles(connection)

        frequent_domain_alerts = create_alerts(domains_and_counts)
        flagged_domain_alerts = create_flagged_domain_alerts(flagged_domains_and_articles)

        alerts = frequent_domain_alerts + flagged_domain_alerts

        wikitext = load_wikitext("https://en.wikipedia.org/wiki/Wikipedia:Vaccine_safety/Alerts?action=raw")

        if wikitext:
            updated_wikitext = insert_alerts(alerts, wikitext)
            final_wikitext = renumber_and_align(updated_wikitext)
            print(final_wikitext)

            update_frequent_domain_notification(connection, domains_and_counts)
            # Update urls.appeared_on_article_notification here (if needed)
            connection.close()

if __name__ == "__main__":
    main()

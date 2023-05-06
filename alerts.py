import pymysql
import requests

# Connect to MySQL database
def create_conn():
    try:
        connection = pymysql.connect(user='your_user',
                                     password='your_password',
                                     host='your_host',
                                     database='database_name')
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
        WHERE urls.last_updated = (SELECT MAX(last_updated) FROM urls)
        GROUP BY urls.domain_id
        HAVING COUNT(urls.domain_id) >= 10 AND domains.frequent_domain_notification IS NULL;
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

def main():
    connection = create_conn()
    if connection:
        domains_and_counts = get_domains_and_counts(connection)
        connection.close()

        alerts = create_alerts(domains_and_counts)
        wikitext = load_wikitext("https://en.wikipedia.org/wiki/Wikipedia:Vaccine_safety/Alerts?action=raw")

        if wikitext:
            updated_wikitext = insert_alerts(alerts, wikitext)
            print(updated_wikitext)

if __name__ == "__main__":
    main()
import re
import requests
from utility import *
from db import *

def get_domains_and_counts(connection):
    """
    Retrieves domain names and number of usages from the database.

    Args:
        connection (pymysql.connections.Connection): Database connection.

    Returns:
        List[Tuple[int, str, int]]: List of tuples containing domain_id, domain name, and count.
    """
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

def insert_alerts(alerts, wikitext):
    """
    Inserts the new alerts into the existing wikitext.

    Args:
        alerts (List[str]): List of new alerts to be inserted.
        wikitext (str): The current wikitext.

    Returns:
        str: Updated wikitext with new alerts inserted.
    """
    start_index = wikitext.index("{{Alert list") + len("{{Alert list")

    for alert in reversed(alerts):
        wikitext = wikitext[:start_index] + "\n" + alert + wikitext[start_index:]

    return wikitext

def load_wikitext(url):
    """
    Fetches wikitext from the specified URL.

    Args:
        url (str): URL to fetch the wikitext from.

    Returns:
        str: Wikitext fetched from the URL or None if there is an error.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error while loading wikitext from URL: {response.status_code}")
        return None

def renumber_and_align(wikitext):
    """
    Renumber the notifications and align the parameter names, equal signs, and values in the wikitext.

    Args:
        wikitext (str): The misnumbered wikitext

    Returns:
        str: Renumbered and aligned wikitext.
    """
    lines = wikitext.split('\n')
    counter = 1

    for i, line in enumerate(lines):
        if re.match(r'\| type\d+ *=', line):
            lines[i] = f"| type{counter}   =" + line.split('=', 1)[1]
            counter += 1

        for param in ['msg', 'action', 'time']:
            if re.match(fr'\| {param}\d+ *=', line):
                lines[i] = f"| {param}{counter - 1}   =" + line.split('=', 1)[1]

    return '\n'.join(lines)

def get_flagged_domains_and_articles(connection):
    """
    Retrieves flagged domains and articles from the database.

    Args:
        connection (pymysql.connections.Connection): Database connection.

    Returns:
        List[Tuple[str, int, str]]: List of tuples containing domain, status, and url_appeared_on.
    """
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

def format_alert_string(i, type_line, msg_line, action_line, time_line):
    """
    Formats template parameters with given parameters.

    Args:
        i (int): Alert index.
        type_line (str): Alert "type" parameter.
        msg_line (str): Alert "message" parameter.
        action_line (str): Alert "action" parameter.
        time_line (str): Alert "time" parameter.

    Returns:
        str: Formatted alert string.
    """
    return f"""| type{i}   = {type_line}
| msg{i}     = {msg_line}
| action{i}  = {action_line}
| time{i}    = {time_line}"""

def create_alerts(alert_type, data):
    """
    Creates template parameters for Alert list call

    Args:
        alert_type (str): Type of the alert ("frequent-domain" or "flagged-domain").
        data (List[Tuple]): List of tuples containing the data to generate alerts.

    Returns:
        List[str]: List of alert strings.
    """
    alerts = []

    for i, item in enumerate(data, 1):
        if alert_type == "frequent-domain":
            domain_id, domain, count = item
            type_line = alert_type
            msg_line = f"'''{domain}''' appears {count} times on articles"
            action_line = "[[Wikipedia:Vaccine safety/Reports#Frequent domain use|view report]]"

        elif alert_type == "flagged-domain":
            domain, status, article = item
            article = to_wikilinks(article).replace('[[', '').replace(']]', '')
            history_link = get_history_link(article)
            type_line = alert_type
            msg_line = f"'''{domain}''' (marked as {{{{vsrate|{status_to_template[status]}}}}}) appears in '''[[{article}]]'''"
            action_line = f"[{history_link} view article history]"

        time_line = "~~~~~"
        alert = format_alert_string(i, type_line, msg_line, action_line, time_line)
        alerts.append(alert)

    return alerts

def get_alerts_page():
    """
    Generates the updated alerts page wikitext with new frequent-domain and flagged-domain alerts.

    Returns:
        str: Updated alerts page wikitext.
    """
    connection = create_conn()
    if connection:
        domains_and_counts = get_domains_and_counts(connection)
        flagged_domains_and_articles = get_flagged_domains_and_articles(connection)

        frequent_domain_alerts = create_alerts("frequent-domain", domains_and_counts)
        flagged_domain_alerts = create_alerts("flagged-domain", flagged_domains_and_articles)

        alerts = frequent_domain_alerts + flagged_domain_alerts

        wikitext = load_wikitext("https://en.wikipedia.org/wiki/Wikipedia:Vaccine_safety/Alerts?action=raw")

        if wikitext:
            updated_wikitext = insert_alerts(alerts, wikitext)
            final_wikitext = renumber_and_align(updated_wikitext)
            print(final_wikitext)

            update_column_with_conditions(
                connection,
                "domains",
                "frequent_domain_notification",
                1,
                [(("id", domain_id),) for domain_id, _, _ in domains_and_counts]
            )

            update_column_with_conditions(
                connection,
                "urls",
                "appeared_on_article_notification",
                1,
                [(("domain_id", domain), ("url_appeared_on", article)) for domain, _, article in flagged_domains_and_articles]
            )

            connection.close()
            return final_wikitext

if __name__ == "__main__":
    get_alerts_page()

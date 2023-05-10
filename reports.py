from utility import *
from db import *

# Connect to the MySQL database
connection = create_conn()
cursor = connection.cursor() if connection is not None else None

def get_last_updated():
    """
    Retrieves the most recent 'last updated' timestamp in the 'urls' table.

    Returns:
        int: The maximum last_updated value from the 'urls' table.
    """
    max_last_updated_query = '''
    SELECT MAX(last_updated) as max_last_updated
    FROM urls
    '''
    return execute_scalar(connection, max_last_updated_query)

def generate_wikipage():
    """
    Generates wiki page content based on several database queries.

    Returns:
        str: The wiki page content as a formatted string.
    """
    last_updated = get_last_updated()

    articles_in_scope_query = '''
        SELECT COUNT(DISTINCT url_appeared_on) as articles_in_scope
        FROM urls
        WHERE last_updated = %s
    '''

    domains_linked_query = '''
        SELECT COUNT(DISTINCT domain) FROM urls u
        JOIN domains d ON u.domain_id = d.id
        WHERE u.last_updated = %s
    '''

    links_to_known_reliable_sources_query = '''
        SELECT ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM urls WHERE last_updated = %s)), 1)
               as links_to_known_reliable_sources
        FROM urls u
        JOIN domains d ON u.domain_id = d.id
        WHERE d.status IN (1, 2) AND u.last_updated = %s
    '''

    links_to_unknown_domains_query = '''
        SELECT ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM urls WHERE last_updated = %s)), 1)
               as links_to_unknown_domains
        FROM urls u
        JOIN domains d ON u.domain_id = d.id
        WHERE d.status IS NULL AND u.last_updated = %s
    '''

    links_to_flagged_sources_query = '''
        SELECT ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM urls WHERE last_updated = %s)), 1)
               as links_to_flagged_sources
        FROM urls u
        JOIN domains d ON u.domain_id = d.id
        WHERE d.status IN (3, 4, 5, 6) AND u.last_updated = %s
    '''

    flagged_domains_query = '''
        SELECT d.domain, d.status, GROUP_CONCAT(DISTINCT u.url_appeared_on) as urls_appeared_on
        FROM urls u
        JOIN domains d ON u.domain_id = d.id
        WHERE d.status IN (3, 4, 5, 6) AND u.last_updated = %s
        GROUP BY d.domain
    '''

    frequent_domains_query = '''
        SELECT d.domain, COUNT(u.id) as url_count, GROUP_CONCAT(DISTINCT u.url_appeared_on) as urls_appeared_on
        FROM urls u
        JOIN domains d ON u.domain_id = d.id
        WHERE d.status IS NULL AND u.last_updated = %s
        GROUP BY d.domain
        HAVING COUNT(u.id) >= 10
        ORDER BY url_count DESC
    '''

    articles_in_scope = execute_scalar(
        connection, articles_in_scope_query, params=(last_updated,)
    )
    domains_linked = execute_scalar(
        connection, domains_linked_query, params=(last_updated,)
    )
    links_to_known_reliable_sources = execute_scalar(
        connection,
        links_to_known_reliable_sources_query,
        params=(last_updated, last_updated)
    )
    links_to_unknown_domains = execute_scalar(
        connection,
        links_to_unknown_domains_query,
        params=(last_updated, last_updated)
    )
    links_to_flagged_sources = execute_scalar(
        connection,
        links_to_flagged_sources_query,
        params=(last_updated, last_updated)
    )
    flagged_domains = execute_query(
        connection, flagged_domains_query, params=(last_updated,)
    )
    frequent_domains = execute_query(
        connection, frequent_domains_query, params=(last_updated,)
    )


    # Close the connection to the database
    if cursor:
        cursor.close()
    if connection:
        connection.close()

    # Create the wiki page content
    wiki_page = f"""
<onlyinclude>{{{{VSAFE metrics dashboard
| articles = {articles_in_scope}
| domains = {domains_linked}
| percent_reliable = {links_to_known_reliable_sources}
| percent_flagged = {links_to_flagged_sources}
| percent_unknown = {links_to_unknown_domains}
}}}}</onlyinclude>

==Frequent domain use==
{{| class="wikitable sortable"
! Domain
! Count
! Appears on articles
|-
"""

    for domain, url_count, urls_appeared_on in frequent_domains:
        wiki_page += f"""
| {domain}
| {url_count}
| {{{{hidden|1=Article links|content={to_wikilinks(urls_appeared_on)}}}}}
|-
"""

    wiki_page += """
|}

==Flagged domain use==
{| class="wikitable sortable"
! Domain
! Status
! Appears on articles
|-
"""

    for domain, status, urls_appeared_on in flagged_domains:
        wiki_page += f"""
| {domain}
| {{{{vsrate|{status_to_template[status]}}}}}
| {{{{hidden|1=Article links|content={to_wikilinks(urls_appeared_on)}}}}}
|-
"""

    wiki_page += """
|}
"""

    return wiki_page

# Print the wiki page content
if __name__ == '__main__':
    print(generate_wikipage())

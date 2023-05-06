import pymysql
from credentials import username, password

# Configure database connection
db_config = {
    'host': 'tools.db.svc.wikimedia.cloud',
    'user': username,
    'password': password,
    'database': 's55412__cited_urls_p',
}

# Connect to the MySQL database
conn = pymysql.connect(**db_config)
cursor = conn.cursor()

# Function to execute query and fetch scalar result
def execute_scalar(query):
    cursor.execute(query)
    return cursor.fetchone()[0]

# Function to execute query and fetch results as list of tuples
def execute_query(query):
    cursor.execute(query)
    return cursor.fetchall()

def to_wikilinks(url_string):
    url_string = url_string.replace(',https://', '\thttps://')
    urls = url_string.split('\t')
    wikilinks = []
    for url in urls:
        url = url.strip()
        title = url.split('/')[-1].replace('_', ' ')
        wikilink = f"[[{title}]]"
        wikilinks.append(wikilink)
    formatted_links = ', '.join(wikilinks)
    return formatted_links

def generate_wikipage():
    articles_in_scope_query = '''
    SELECT COUNT(DISTINCT url_appeared_on) as articles_in_scope
    FROM urls
    '''
    articles_in_scope = execute_scalar(articles_in_scope_query)

    domains_linked_query = '''
    SELECT COUNT(DISTINCT domain) as domains_linked
    FROM domains
    '''
    domains_linked = execute_scalar(domains_linked_query)

    links_to_known_reliable_sources_query = '''
    SELECT ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM urls)), 1)
           as links_to_known_reliable_sources
    FROM urls u
    JOIN domains d ON u.domain_id = d.id
    WHERE d.status IN (1, 2)
    '''
    links_to_known_reliable_sources = execute_scalar(links_to_known_reliable_sources_query)

    links_to_unknown_domains_query = '''
    SELECT ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM urls)), 1)
           as links_to_unknown_domains
    FROM urls u
    JOIN domains d ON u.domain_id = d.id
    WHERE d.status IS NULL
    '''
    links_to_unknown_domains = execute_scalar(links_to_unknown_domains_query)

    links_to_flagged_sources_query = '''
    SELECT ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM urls)), 1)
           as links_to_flagged_sources
    FROM urls u
    JOIN domains d ON u.domain_id = d.id
    WHERE d.status IN (3, 4, 5, 6)
    '''
    links_to_flagged_sources = execute_scalar(links_to_flagged_sources_query)

    # Get flagged domains and their uses
    flagged_domains_query = '''
    SELECT d.domain, d.status, GROUP_CONCAT(DISTINCT u.url_appeared_on) as urls_appeared_on
    FROM urls u
    JOIN domains d ON u.domain_id = d.id
    WHERE d.status IN (3, 4, 5, 6)
    GROUP BY d.domain
    '''
    flagged_domains = execute_query(flagged_domains_query)

    # Get frequent domains and their use
    frequent_domains_query = '''
    SELECT d.domain, COUNT(u.id) as url_count, GROUP_CONCAT(DISTINCT u.url_appeared_on) as urls_appeared_on
    FROM urls u
    JOIN domains d ON u.domain_id = d.id
    WHERE d.status IS NULL
    GROUP BY d.domain
    HAVING COUNT(u.id) >= 10
    ORDER BY url_count
    '''
    frequent_domains = execute_query(frequent_domains_query)

    # Close the connection to the database
    cursor.close()
    conn.close()

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
| {status}
| {{{{hidden|1=Article links|content={to_wikilinks(urls_appeared_on)}}}}}
|-
"""

    wiki_page += """
|}
"""

    return wiki_page

# Print the wiki page content
print(generate_wikipage())

import requests
from wikidataintegrator import wdi_core, wdi_login
from credentials import wikibase_username, wikibase_password

def wikibase_domains_query():
    query = '''
    PREFIX wdt: <https://domains.wikibase.cloud/prop/direct/>
    PREFIX wd: <https://domains.wikibase.cloud/entity/>

    SELECT ?item ?P1_value
    WHERE {
      ?item wdt:P1 ?P1_value .
    }
    '''

    url = 'https://domains.wikibase.cloud/query/sparql'
    response = requests.get(url, params={'query': query, 'format': 'json'})
    return response.json()

def fetch_wikidata_official_websites():
    query = '''
    SELECT ?item ?website
    WHERE {
      ?item wdt:P856 ?website .
    }
    '''

    url = 'https://sparql.orb.rest/bigdata/namespace/wdq/sparql'
    response = requests.get(url, params={'query': query, 'format': 'json'})
    return response.json()

def is_root_domain(official_website, domain):
    url_without_domain = official_website[len(domain):]
    return not url_without_domain or url_without_domain == "/" or url_without_domain.startswith("/?")

def update_wikibase_item(wikibase_item, wikidata_item):
    login_instance = wdi_login.WDLogin(
        user=wikibase_username,
        pwd=wikibase_password,
        mediawiki_api_url="https://domains.wikibase.cloud/w/api.php",
        mediawiki_index_url="https://domains.wikibase.cloud/w/index.php",
        user_agent="YourAppName/1.0 (yourname@example.com)"
    )

    item_data = [
        wdi_core.WDString(value=wikidata_item, prop_nr="P2")
    ]

    item = wdi_core.WDItemEngine(
        wd_item_id=wikibase_item,
        data=item_data,
        mediawiki_api_url="https://domains.wikibase.cloud/w/api.php",
        sparql_endpoint_url="https://domains.wikibase.cloud/query/sparql"
    )

    item.write(login_instance)

def main():
    prefixes = ["http://", "https://", "http://www.", "https://www."]
    domain_results = wikibase_domains_query()
    
    wikidata_websites = fetch_wikidata_official_websites()
    websites_dict = {}

    for website in wikidata_websites['results']['bindings']:
        item = website['item']['value'].split('/')[-1]
        official_website = website['website']['value']
        websites_dict[official_website] = item

    for result in domain_results['results']['bindings']:
        wikibase_item = result['item']['value'].split('/')[-1]
        domain = result['P1_value']['value']
        domain = domain.replace('www.', '')

        for prefix in prefixes:
            full_domain = prefix + domain
            
            if full_domain in websites_dict and is_root_domain(full_domain, full_domain):
                wikidata_item = websites_dict[full_domain]
                update_wikibase_item(wikibase_item, wikidata_item)

if __name__ == "__main__":
    main()

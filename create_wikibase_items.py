import requests
from wikidataintegrator import wdi_core, wdi_login
from credentials import wikibase_username, wikibase_password
from db import *

# Set up SPARQL query
sparql_endpoint = "https://domains.wikibase.cloud/query/sparql"
query = """
PREFIX wdt: <https://domains.wikibase.cloud/prop/direct/>
PREFIX wd: <https://domains.wikibase.cloud/entity/>

SELECT ?item ?P1_value
WHERE {
  ?item wdt:P1 ?P1_value .
}
"""
response = requests.get(sparql_endpoint, params={'query': query, 'format': 'json'})
results = response.json()

# Get existing domain mapping
existing_domains = {
    result['P1_value']['value']: result['item']['value']
    for result in results['results']['bindings']
}

# Set up MySQL connection
connection = create_conn()
cursor = connection.cursor()

# Query MySQL table
query = "SELECT domain, status, perennial_source FROM domains"
cursor.execute(query)

# Status mapping
status_mapping = {1: "Q2", 2: "Q3", 3: "Q4", 4: "Q5", 5: "Q6", 6: "Q7"}

for row in cursor:
    domain, status, perennial_source = row

    # Check if domain is already in Wikibase
    if domain not in existing_domains:
        # Create new Wikibase item
        item_data = [
            wdi_core.WDString(value=domain, prop_nr="P1"),
        ]

        qualifiers = {}
        if status is not None and status > 0:
            qualifiers["P8"] = status_mapping.get(status)

        if perennial_source == 1:
            qualifiers_list = [
                wdi_core.WDItemID(
                    prop_nr=prop_nr, value=value, is_qualifier=True
                ) for prop_nr, value in qualifiers.items()
            ]
            item_data.append(wdi_core.WDUrl(
                value="https://en.wikipedia.org/wiki/Wikipedia:Vaccine_safety/Perennial_sources",
                prop_nr="P7",
                qualifiers=qualifiers_list
            ))

        # Save new Wikibase item and print ID
        new_item = wdi_core.WDItemEngine(
            data=item_data
        )
        # Set up WikidataIntegrator login
        login_instance = wdi_login.WDLogin(
            user=wikibase_username,
            pwd=wikibase_password,
            mediawiki_api_url="https://domains.wikibase.cloud/w/api.php",
            mediawiki_index_url="https://domain.wikibase.cloud/w/index.php",
            user_agent="Vsafe-Data/1.0 (james@scatter.red)"
        )
        new_item.write(login_instance)
        print(f"Created new Wikibase item with ID: {new_item.wd_item_id}")

# Close MySQL connection
cursor.close()
connection.close()

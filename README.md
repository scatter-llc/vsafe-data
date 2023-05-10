This repository includes:
* Credibility bot, which updates reports of source usage on Wikipedia.
* Scripts for contributing data to the Internet Domains Wikibase

## Setup

1. `git clone https://github.com/scatter-llc/vsafe-data`

2. `cd vsafe-data`

3. `python3 -m venv venv`

4. `source venv/bin/activate`

5. `pip3 install -r requirements.txt`

6. Create a MySQL (or MariaDB) database if you have not yet. (Schema forthcoming)

7. Set up `credentials.py` (for database and Domains Wikibase access) like this:

```
username = 'your_mysql_username'
password = 'your_mysql_password'
dbname = 'your_database_name'
hostname = 'mysql_database_server_address'
wikibase_username = 'your_username_on_domains_wikibase'
wikibase_password = 'your_password_on_domains_wikibase'
```

8. Set up `user-config.py` (for pywikibot, for updating Wikipedia) like this:

```
mylang = 'en'
family = 'wikipedia'
usernames['wikipedia']['en'] = 'your_username'
password_file = 'pywikibot-password.txt'
```

9. Set up `pywikibot-password.txt` like this:

```
('your_wikipedia_username', 'your_wikipedia_password')
```

Note: You are encouraged to use a bot password <https://en.wikipedia.org/wiki/Special:BotPasswords>.

## Operation

Process the perennial sources table at <https://en.wikipedia.org/wiki/Wikipedia:Vaccine_safety/Perennial_sources> and produce a CSV:

```
python3 parse_wikitable.py > file.csv
```

Take the resulting CSV and add it to the references database:

```
python3 process_csv.py file.csv
```

Update the references database and post reports and alerts:

```
python3 bot.py
```

Create new items in the Domains Wikibase based on domains in the references database:

```
python3 create_wikibase_items.py
```

Update the mapping of Domains Wikibase items and Wikidata items via "official property"

```
python3 map_official_domain.py
```
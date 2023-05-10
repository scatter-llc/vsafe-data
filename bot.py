import check_references, reports, alerts
import pywikibot

def main():
    # Refreshing reference database
    check_references.go()

    # Generating contents of [[Wikipedia:Vaccine safety/Reports]]
    Reports_content = reports.generate_wikipage()

    # Update [[Wikipedia:Vaccine Safety/Reports]] page
    update_wiki_page("Wikipedia:Vaccine safety/Reports", Reports_content)

    # Generating contents of [[Wikipedia:Vaccine safety/Alerts]]
    Alerts_content = alerts.get_alerts_page()

    # Update [[Wikipedia:Vaccine Safety/Alerts]] page
    update_wiki_page("Wikipedia:Vaccine safety/Alerts", Alerts_content)

def update_wiki_page(page_title, new_content):
    site = pywikibot.Site()
    page = pywikibot.Page(site, page_title)
    
    # Check if the page exists and if the new content is different
    if page.exists() and page.text != new_content:
        page.text = new_content
        page.save(f"Updating {page_title} with new content")
        print(f"{page_title} has been updated.")
    else:
        print(f"{page_title} does not exist or has no changes.")

if __name__ == '__main__':
    main()

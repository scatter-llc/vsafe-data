import requests
import csv
import sys

def get_table_row():
    url = "https://en.wikipedia.org/wiki/Wikipedia:Vaccine_safety/Perennial_sources?action=raw"

    response = requests.get(url)

    if response.status_code == 200:
        content = response.text.splitlines()
        table_rows = []

        for line in content:
            if line.startswith("|"):
                if line == "|-":
                    table_rows.append([])
                else:
                    table_rows[-1].append(line[1:].strip())

        for row in table_rows:
            if row == []:
                continue
            output_row = [
                row[0], # type
                row[1], # name
                row[2], # url
                row[4], # assessmentStatus
                row[5], # assessmentSummary
            ]
            yield output_row
    else:
        raise Exception(f"Error: Unable to fetch content. Status code: {response.status_code}")

def print_csv_table():
    header = ["row_type", "row_source_name", "row_url", "row_status", "row_comment"]

    csv_writer = csv.writer(sys.stdout)
    csv_writer.writerow(header)

    for row in get_table_row():
        csv_writer.writerow(row)

if __name__ == '__main__':
    print_csv_table()

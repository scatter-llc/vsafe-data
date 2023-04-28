import csv
import re
import mysql.connector

def process_csv(input_file):
    output_rows = []
    with open(input_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            processed_row = {}
            # Process row_type
            processed_row["typeOfSource"] = row["row_type"].lower()
            if processed_row["typeOfSource"] == "gov":
                processed_row["typeOfSource"] = "government"

            bracket_match = re.search(r'\[\[(.*?)\]\]', row["row_source_name"])
            if bracket_match:
                if '|' in bracket_match.group(1):
                    name = bracket_match.group(1).split('|')[1]
                else:
                    name = bracket_match.group(1)
                processed_row["name"] = name
            else:
                processed_row["name"] = row["row_source_name"]

            # Process row_url
            urls = re.findall(r'(https?://\S+)', row["row_url"])
            if urls:
                processed_row["url"] = urls[0]
                if len(urls) > 1:
                    processed_row["url_alt"] = urls[1]

            # Process row_status
            ref_matches = re.findall(r'<ref.*?\/>|<ref.*?>.*?<\/ref>', row["row_status"])
            if ref_matches:
                processed_row["assessmentFootnote"] = " ".join(ref_matches)
                for match in ref_matches:
                    row["row_status"] = row["row_status"].replace(match, "").strip()

            assessment_match = re.search(r'{{vsrate\|(.*?)(\||})', row["row_status"])
            if assessment_match:
                processed_row["assessmentStatus"] = assessment_match.group(1)

            # Process row_comment
            ref_matches = re.findall(r'<ref.*?\/>|<ref.*?>.*?<\/ref>', row["row_comment"])
            if ref_matches:
                processed_row["discussionSummaryFootnote"] = " ".join(ref_matches)
                for match in ref_matches:
                    row["row_comment"] = row["row_comment"].replace(match, "").strip()

            processed_row["discussionSummary"] = row["row_comment"]
            output_rows.append(processed_row)

    return output_rows

def write_csv(output_file, output_rows):
    fieldnames = ["typeOfSource", "name", "url", "url_alt", "assessmentStatus",
                  "assessmentFootnote", "discussionSummary", "discussionSummaryFootnote"]
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

def prep_csv_for_sql(input_file):
    output_rows = []
    with open(input_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            processed_row = {}
            # Process row_url
            urls = row["url"].replace("https://", "").replace("http://", "").split("/")
            processed_row["domain"] = urls[0]

            # Process row_status
            if "assessmentStatus" in row:
                status = row["assessmentStatus"].lower()
                if status == "pending":
                    processed_row["status"] = 0
                elif status == "vsn":
                    processed_row["status"] = 1
                elif status == "reliable":
                    processed_row["status"] = 2
                elif status == "mixed":
                    processed_row["status"] = 3
                elif status == "unreliable":
                    processed_row["status"] = 4
                elif status == "conspiracy":
                    processed_row["status"] = 5
                elif status == "blocked":
                    processed_row["status"] = 6
                else:
                    processed_row["status"] = None

            processed_row["perennial_source"] = 1
            output_rows.append(processed_row)

    return output_rows

def insert_into_db(rows):
    try:
        conn = mysql.connector.connect(user='<username>', password='<password>',
                                        host='tools.db.svc.wikimedia.cloud', database='s55412__cited_urls_p')
        cursor = conn.cursor()

        for row in rows:
            if row['status'] is not None:
                sql = """INSERT INTO domains (domain, status, perennial_source) 
                            VALUES (%s, %s, %s)"""
                val = (row['domain'], row['status'], row['perennial_source'])
                cursor.execute(sql, val)
                conn.commit()

        cursor.close()

    except Exception as e:
        print(f"Error inserting data into the database: {e}")

    finally:
        if conn.is_connected():
            conn.close()

input_file = '2023-04-12-run01-derived.csv'
output_rows = prep_csv_for_sql(input_file)
insert_into_db(output_rows)
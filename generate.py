import urllib.request
import csv
import os

# 1. LINK TO YOUR GOOGLE SHEET CSV (We will put your real URL here soon)
CSV_URL = "REPLACE_WITH_YOUR_CSV_URL"

def download_and_generate():
    # Create the folder where Vercel will look for web pages
    output_dir = "public"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the master story template you just saved
    with open("template.txt", "r", encoding="utf-8") as f:
        template_content = f.read()

    print("Fetching latest records from Google Sheets...")
    
    # Securely download the live Google Sheet spreadsheet data from the cloud
    response = urllib.request.urlopen(CSV_URL)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    count = 0
    for row in reader:
        # Clean up names to make pretty URLs (e.g., "Austin, Texas" -> "austin-texas.html")
        city_slug = row['city'].strip().lower().replace(' ', '-')
        state_slug = row['state'].strip().lower().replace(' ', '-')
        filename = f"{city_slug}-{state_slug}.html"

        # Drop the spreadsheet facts into the matching bracket spaces
        html_page = template_content.format(
            city=row['city'].strip(),
            state=row['state'].strip(),
            survey_cost=row['survey_cost'].strip(),
            permit_days=row['permit_days'].strip(),
            zoning_office=row['zoning_office'].strip(),
            growth_type=row['growth_type'].strip()
        )

        # Save the finished page into the public folder
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as out_file:
            out_file.write(html_page)
        count += 1

    print(f"Success! {count} programmatic pages generated in the cloud.")

if __name__ == "__main__":
    download_and_generate()

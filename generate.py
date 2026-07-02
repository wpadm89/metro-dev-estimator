import urllib.request
import csv
import os

# 1. LINK TO YOUR GOOGLE SHEET CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQMP8m4tpMGQBUVzJTFeDafKYHmxvLZss9r369IWWU6t9slrcXX8e7w1qjl-snipjpLoF7TniA-7QlV/pub?gid=0&single=true&output=csv"

def download_and_generate():
    output_dir = "public"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the master story template
    with open("template.txt", "r", encoding="utf-8") as f:
        template_content = f.read()

    print("Fetching latest records from Google Sheets...")
    
    response = urllib.request.urlopen(CSV_URL)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    count = 0
    homepage_links_html = "" # This will collect all our dynamic homepage links

    for row in reader:
        city_name = row['city'].strip()
        state_name = row['state'].strip()
        
        # Clean up names to make pretty URLs
        city_slug = city_name.lower().replace(' ', '-')
        state_slug = state_name.lower().replace(' ', '-')
        filename = f"{city_slug}-{state_slug}.html"

        # Drop the spreadsheet facts into the matching template spaces
        html_page = template_content.format(
            city=city_name,
            state=state_name,
            survey_cost=row['survey_cost'].strip(),
            permit_days=row['permit_days'].strip(),
            zoning_office=row['zoning_office'].strip(),
            growth_type=row['growth_type'].strip()
        )

        # Save the finished page into the public folder
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as out_file:
            out_file.write(html_page)
        
        # ANTIGRAVITY AUTOMATION: Add this city link to our list for the homepage
        homepage_links_html += f'        <li style="margin: 10px 0;"><a href="/{filename}" style="color: #0070f3; text-decoration: none; font-size: 1.1rem; font-weight: bold;">{city_name}, {state_name} Cost Estimator Guide</a></li>\n'
        count += 1

    # Define the beautiful, dynamic homepage layout
    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Commercial Development Cost Directory</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px;">
    <h1 style="color: #111; border-bottom: 2px solid #eee; padding-bottom: 10px;">US Commercial Development Cost Directory</h1>
    <p style="font-size: 1.1rem; color: #555;">Select a regional structural estimation and layout guide below:</p>
    <ul style="list-style-type: square; padding-left: 20px;">
{homepage_links_html}    </ul>
</body>
</html>"""

    # Save the automatically built homepage into the public folder
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as index_file:
        index_file.write(index_html_content)

    print(f"Success! Built homepage and {count} programmatic pages in the cloud.")

if __name__ == "__main__":
    download_and_generate()

import urllib.request
import csv
import os

# 1. LINK TO YOUR GOOGLE SHEET CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQMP8m4tpMGQBUVzJTFeDafKYHmxvLZss9r369IWWU6t9slrcXX8e7w1qjl-snipjpLoF7TniA-7QlV/pub?gid=0&single=true&output=csv"
BASE_URL = "https://metro-dev-estimator.vercel.app"

def download_and_generate():
    output_dir = "public"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the master template
    with open("template.txt", "r", encoding="utf-8") as f:
        template_content = f.read()

    print("Fetching latest records from Google Sheets...")
    
    response = urllib.request.urlopen(CSV_URL)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    count = 0
    homepage_links_html = ""
    
    # Initialize the automated XML sitemap structure
    sitemap_xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    # Add the homepage to the map first
    sitemap_xml_content += f'    <url>\n        <loc>{BASE_URL}/</loc>\n        <priority>1.0</priority>\n    </url>\n'

    for row in reader:
        city_name = row['city'].strip()
        state_name = row['state'].strip()
        
        # Clean up names to make pretty URLs
        city_slug = city_name.lower().replace(' ', '-')
        state_slug = state_name.lower().replace(' ', '-')
        filename = f"{city_slug}-{state_slug}.html"

        # DYNAMIC MATH: Extract numbers safely and calculate credible ranges
        try:
            clean_cost = int(row['survey_cost'].replace('$', '').replace(',', '').strip())
            clean_days = int(row['permit_days'].strip())
        except ValueError:
            clean_cost = 3500
            clean_days = 20

        # Calculate a low/high variance band for Surveying Costs (-15% to +25%)
        survey_low = f"${int(clean_cost * 0.85):,}"
        survey_high = f"${int(clean_cost * 1.25):,}"

        # Calculate a low/high variance band for Permit Timelines (-4 days to +20 days)
        permit_low = max(5, clean_days - 4)
        permit_high = clean_days + 20

        # Drop the computed ranges into the updated template slots
        html_page = template_content.format(
            city=city_name,
            state=state_name,
            survey_low=survey_low,
            survey_high=survey_high,
            permit_low=permit_low,
            permit_high=permit_high,
            zoning_office=row['zoning_office'].strip(),
            growth_type=row['growth_type'].strip()
        )

        # Save the finished page into the public folder
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as out_file:
            out_file.write(html_page)
        
        # Track dynamic homepage links
        homepage_links_html += f'        <li style="margin: 10px 0;"><a href="/{filename}" style="color: #0070f3; text-decoration: none; font-size: 1.1rem; font-weight: bold;">{city_name}, {state_name} Cost Estimator Guide</a></li>\n'
        
        # Append this city's URL directly into the dynamic sitemap mapping array
        sitemap_xml_content += f'    <url>\n        <loc>{BASE_URL}/{filename}</loc>\n        <priority>0.8</priority>\n    </url>\n'
        count += 1

    # Close out the XML sitemap structure
    sitemap_xml_content += "</urlset>"

    # Define the dynamic homepage layout with AdSense verification included
    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Commercial Development Cost Directory</title>
    
    <!-- 💰 ADSENSE HOME PAGE VERIFICATION -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4339332173825521" crossorigin="anonymous"></script>
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

    # Write the completely built sitemap directly into production storage
    with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as sitemap_file:
        sitemap_file.write(sitemap_xml_content)

    print(f"Success! Built directory maps and {count} programmatic pages in the cloud.")

if __name__ == "__main__":
    download_and_generate()

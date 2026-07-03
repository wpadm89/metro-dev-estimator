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
    raw_data = response.read().decode('utf-8')
    
    # Process data rows out of raw lines
    lines = raw_data.splitlines()
    
    # Pass 1: Build a relationship map of all cities grouped by their state for the SEO Grid
    state_groups = {}
    reader_pre = csv.DictReader(lines)
    for row in reader_pre:
        s_name = row['state'].strip()
        c_name = row['city'].strip()
        c_slug = c_name.lower().replace(' ', '-')
        s_slug = s_name.lower().replace(' ', '-')
        f_name = f"{c_slug}-{s_slug}.html"
        
        if s_name not in state_groups:
            state_groups[s_name] = []
        state_groups[s_name].append({"city": c_name, "filename": f_name})

    # Pass 2: Reset reader and build pages cleanly
    reader = csv.DictReader(lines)
    count = 0
    homepage_links_html = ""
    
    # Initialize the automated XML sitemap structure
    sitemap_xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml_content += f'    <url>\n        <loc>{BASE_URL}/</loc>\n        <priority>1.0</priority>\n    </url>\n'

    for row in reader:
        city_name = row['city'].strip()
        state_name = row['state'].strip()
        zoning_office_name = row['zoning_office'].strip()
        
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

        survey_low = f"${int(clean_cost * 0.85):,}"
        survey_high = f"${int(clean_cost * 1.25):,}"
        permit_low = max(5, clean_days - 4)
        permit_high = clean_days + 20

        # Build the HTML internal navigation module for this page's state group
        grid_html = f'<div style="margin-top: 40px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px;">\n'
        grid_html += f'    <h4 style="margin: 0 0 10px 0; color: #334155; font-size: 1.1rem;">Other Regional Estimators in {state_name}:</h4>\n'
        grid_html += f'    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px;">\n'
        
        for peer in state_groups[state_name]:
            if peer['city'] != city_name: 
                grid_html += f'        <a href="/{peer["filename"]}" style="color: #2563eb; text-decoration: none; font-size: 0.9rem;">• {peer["city"]} Cost Estimate</a>\n'
        
        grid_html += '    </div>\n</div>'

        # Generate the JSON-LD Local business FAQ structured metadata
        schema_json = f"""<script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{
          "@type": "Question",
          "name": "How much does a commercial land survey cost in {city_name}?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "The average cost for a standard commercial land boundary and topographic survey in {city_name} typically ranges between {survey_low} and {survey_high} depending on total site acreage and topological complexity."
          }}
        }},
        {{
          "@type": "Question",
          "name": "How long does it take to get a commercial building permit in {city_name}?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "The standard application processing turnaround window to secure civil structural layout or zoning verification approvals via the {zoning_office_name} ranges between {permit_low} to {permit_high} days."
          }}
        }}
      ]
    }}
    </script>"""

        # Drop everything into the master template layout
        html_page = template_content.format(
            city=city_name,
            state=state_name,
            survey_low=survey_low,
            survey_high=survey_high,
            permit_low=permit_low,
            permit_high=permit_high,
            zoning_office=zoning_office_name,
            growth_type=row['growth_type'].strip(),
            state_links_group=grid_html,
            faq_schema_block=schema_json
        )

        # Save finished file
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as out_file:
            out_file.write(html_page)
        
        homepage_links_html += f'        <li style="margin: 10px 0;"><a href="/{filename}" style="color: #0070f3; text-decoration: none; font-size: 1.1rem; font-weight: bold;">{city_name}, {state_name} Cost Estimator Guide</a></li>\n'
        sitemap_xml_content += f'    <url>\n        <loc>{BASE_URL}/{filename}</loc>\n        <priority>0.8</priority>\n    </url>\n'
        count += 1

    sitemap_xml_content += "</urlset>"

    # Define the dynamic homepage directory layout
    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Commercial Development Cost Directory</title>
    
    <!-- 🔍 GOOGLE SEARCH CONSOLE VERIFICATION -->
    <meta name="google-site-verification" content="94MKhhJxy6J9jbZVtS2AynrkXcKfpD7JR-mHnFB7-QQ" />
    
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

    # Write Index
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as index_file:
        index_file.write(index_html_content)

    # Write Sitemap
    with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as sitemap_file:
        sitemap_file.write(sitemap_xml_content)

    # 💰 AUTOMATED ADS.TXT INJECTION FOR ANTI-FRAUD CLEARANCE
    ads_txt_content = "google.com, pub-4339332173825521, DIRECT, f08c47fec0942fa0"
    with open(os.path.join(output_dir, "ads.txt"), "w", encoding="utf-8") as ads_txt_file:
        ads_txt_file.write(ads_txt_content)

    print(f"Success! Built directory maps, sitemaps, ads.txt, schema parameters, cross-linking nodes, and {count} programmatic pages in the cloud.")

if __name__ == "__main__":
    download_and_generate()

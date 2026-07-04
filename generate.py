import urllib.request
import csv
import os
import json

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
    lines = raw_data.splitlines()

    # Pass 1: Build state groups and compile list data for the home screen interactive widget
    state_groups = {}
    calculator_dataset = {}
    reader_pre = csv.DictReader(lines)

    for row in reader_pre:
        s_name = row['state'].strip()
        c_name = row['city'].strip()
        c_slug = c_name.lower().replace(' ', '-')
        s_slug = s_name.lower().replace(' ', '-')
        f_name = f"{c_slug}-{s_slug}.html"

        # Group by state for linking grid
        if s_name not in state_groups:
            state_groups[s_name] = []
        state_groups[s_name].append({"city": c_name, "filename": f_name})

        # Standardize calculations for calculator data matrix
        try:
            base_cost = int(row['survey_cost'].replace('$', '').replace(',', '').strip())
            base_days = int(row['permit_days'].strip())
        except (ValueError, KeyError):
            base_cost = 3500
            base_days = 20

        calculator_dataset[f"{c_name}, {s_name}"] = {
            "cost": base_cost,
            "days": base_days,
            "url": f"/{f_name}"
        }

    # Pass 2: Re-read dataset and write pages cleanly
    reader = csv.DictReader(lines)
    count = 0
    homepage_links_html = ""
    dropdown_options_html = ""

    # Form option nodes for the calculator dropdown selector
    for key in sorted(calculator_dataset.keys()):
        dropdown_options_html += f'            <option value="{key}">{key}</option>\n'

    # Initialize the automated XML sitemap structure
    sitemap_xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml_content += f'    <url>\n        <loc>{BASE_URL}/</loc>\n        <priority>1.0</priority>\n    </url>\n'

    for row in reader:
        city_name = row['city'].strip()
        state_name = row['state'].strip()
        zoning_office_name = row['zoning_office'].strip()

        # Option 3 Content Injection with fallbacks
        local_notes = row.get('local_notes', '').strip()
        if not local_notes:
            local_notes = f"When establishing commercial operations within the {city_name} perimeter, structural crews must carefully calculate local infrastructure variables and survey layouts against regional constraints before submitting final architectural submittals."

        city_slug = city_name.lower().replace(' ', '-')
        state_slug = state_name.lower().replace(' ', '-')
        filename = f"{city_slug}-{state_slug}.html"

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

        # Build cross-linking navigation matrix module
        grid_html = f'<div style="margin-top: 40px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px;">\n'
        grid_html += f'    <h4 style="margin: 0 0 10px 0; color: #334155; font-size: 1.1rem;">Other Regional Estimators in {state_name}:</h4>\n'
        grid_html += f'    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px;">\n'

        for peer in state_groups[state_name]:
            if peer['city'] != city_name:
                grid_html += f'        <a href="/{peer["filename"]}" style="color: #2563eb; text-decoration: none; font-size: 0.9rem;">• {peer["city"]} Cost Estimate</a>\n'

        grid_html += '    </div>\n</div>'

        # Generate the JSON-LD FAQ schema metadata
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

        # Format everything into template variables
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
            faq_schema_block=schema_json,
            local_notes=local_notes
        )

        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as out_file:
            out_file.write(html_page)

        homepage_links_html += f'        <li style="margin: 10px 0;"><a href="/{filename}" style="color: #0070f3; text-decoration: none; font-size: 1.1rem; font-weight: bold;">{city_name}, {state_name} Cost Estimator Guide</a></li>\n'
        sitemap_xml_content += f'    <url>\n        <loc>{BASE_URL}/{filename}</loc>\n        <priority>0.8</priority>\n    </url>\n'
        count += 1

    sitemap_xml_content += "</urlset>"

    # 🧮 INTERACTIVE HOME WIDGET ENGINE WITH FLAT NAVIGATION TOGGLE
    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Commercial Development Cost Directory & Calculator</title>
    
    <!-- 🔍 GOOGLE SEARCH CONSOLE VERIFICATION -->
    <meta name="google-site-verification" content="94MKhhJxy6J9jbZVtS2AynrkXcKfpD7JR-mHnFB7-QQ" />
    
    <!-- 💰 ADSENSE HOME PAGE VERIFICATION -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4339332173825521" crossorigin="anonymous"></script>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px;">
    
    <!-- 🔄 NICHE SWITCHER NAVIGATION HEADER -->
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <strong style="color: #0f172a; font-size: 0.95rem;">Active Directory: 🏢 Commercial Costs</strong>
        <a href="/residential" style="color: #10b981; font-weight: bold; text-decoration: none; font-size: 0.95rem;">Switch to 🏡 Residential Surveys &rarr;</a>
    </div>

    <h1 style="color: #111; border-bottom: 2px solid #eee; padding-bottom: 10px;">US Commercial Development Cost Directory</h1>
    
    <!-- 🧮 CALCULATOR PANEL CARD CONTAINER -->
    <div style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; margin: 30px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; color: #1e293b; font-size: 1.3rem;">Instant Regional Project Budget Cost Estimator</h3>
        <p style="color: #475569; font-size: 0.95rem; margin-bottom: 20px;">Select your layout territory and enter project size to estimate scaling ranges:</p>
        
        <div style="display: grid; gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-weight: bold; font-size: 0.85rem; color: #475569; margin-bottom: 5px;">TARGET REGIONAL AREA</label>
                <select id="calc-city" style="width: 100%; padding: 10px; border: 1px solid #94a3b8; border-radius: 4px; font-size: 0.95rem; background: white;">
{dropdown_options_html}                </select>
            </div>
            <div>
                <label style="display: block; font-weight: bold; font-size: 0.85rem; color: #475569; margin-bottom: 5px;">ESTIMATED SITE SIZE (ACRES)</label>
                <input type="number" id="calc-acres" value="1.0" min="0.1" step="0.1" style="width: 100%; padding: 10px; border: 1px solid #94a3b8; border-radius: 4px; box-sizing: border-box; font-size: 0.95rem;">
            </div>
        </div>
        
        <button onclick="calculateBudget()" style="width: 100%; background: #0070f3; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 1rem;">Run Structural Estimator Computations</button>
        
        <!-- CALC OUTPUT BOARD -->
        <div id="calc-results" style="display: none; margin-top: 20px; border-top: 1px dashed #cbd5e1; padding-top: 20px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; text-align: center;">
                <div style="background: white; border-radius: 6px; padding: 15px; border: 1px solid #e2e8f0;">
                    <span style="display:block; font-size: 0.8rem; color: #64748b; font-weight: bold;">SURVEY COST ESTIMATE</span>
                    <strong id="result-cost" style="font-size: 1.4rem; color: #0f172a;">--</strong>
                </div>
                <div style="background: white; border-radius: 6px; padding: 15px; border: 1px solid #e2e8f0;">
                    <span style="display:block; font-size: 0.8rem; color: #64748b; font-weight: bold;">ESTIMATED PERMIT TIMELINE</span>
                    <strong id="result-days" style="font-size: 1.4rem; color: #0f172a;">--</strong>
                </div>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <a id="result-link" href="#" style="color: #0070f3; font-weight: bold; text-decoration: none; font-size: 0.95rem;">Read Full Local Development Guide &rarr;</a>
            </div>
        </div>
    </div>

    <p style="font-size: 1.1rem; color: #555;">Or browse individual programmatic city cost directory logs below:</p>
    <ul style="list-style-type: square; padding-left: 20px;">
{homepage_links_html}    </ul>

    <!-- INTERACTIVE CALC ENGINE OBJECT SCRIPT -->
    <script>
        const dataMatrix = {json.dumps(calculator_dataset)};
        
        function calculateBudget() {{
            const cityKey = document.getElementById('calc-city').value;
            const acres = parseFloat(document.getElementById('calc-acres').value) || 1.0;
            const record = dataMatrix[cityKey];
            
            if(!record) return;
            
            const multiplier = Math.max(0.6, 1 + (Math.log10(acres) * 0.45));
            const computedCost = Math.round(record.cost * acres * multiplier);
            
            const costLow = Math.round(computedCost * 0.85);
            const costHigh = Math.round(computedCost * 1.25);
            
            const permitLow = Math.max(5, record.days - 4);
            const permitHigh = record.days + 20;
            
            document.getElementById('result-cost').innerText = '$' + costLow.toLocaleString() + ' - $' + costHigh.toLocaleString();
            document.getElementById('result-days').innerText = permitLow + ' to ' + permitHigh + ' Days';
            document.getElementById('result-link').href = record.url;
            document.getElementById('calc-results').style.display = 'block';
        }}
    </script>
</body>
</html>"""

    # Write Index
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as index_file:
        index_file.write(index_html_content)

    # Write Sitemap
    with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as sitemap_file:
        sitemap_file.write(sitemap_xml_content)

    # Write robots.txt — points crawlers at both the commercial and
    # residential sitemaps. Written here since generate.py always runs
    # first in the build ("python3 generate.py && python3 generate_residential.py").
    robots_txt_content = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
Sitemap: {BASE_URL}/residential-sitemap.xml
"""

    with open(os.path.join(output_dir, "robots.txt"), "w", encoding="utf-8") as robots_file:
        robots_file.write(robots_txt_content)

    print(f"Success! Built directory maps and {count} commercial programmatic pages.")

if __name__ == "__main__":
    download_and_generate()

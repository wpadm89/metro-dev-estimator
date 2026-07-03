import urllib.request
import csv
import os
import json

# 1. NEW RESIDENTIAL CSV GOOGLE SHEET LINK
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ6Irlr4Q_CdY6iVcQacKeTDROrhXuWOh2rhwKlmO4gjj8SE-zIUhAd_e5VJh2T9HSa8gR4SEERYgaT/pub?output=csv"
BASE_URL = "https://metro-dev-estimator.vercel.app"

def download_and_generate_residential():
    # Set directory path to build pages under public/residential/
    output_dir = os.path.join("public", "residential")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the residential template
    with open("residential_template.txt", "r", encoding="utf-8") as f:
        template_content = f.read()

    print("Fetching records from Residential Google Sheet...")
    
    response = urllib.request.urlopen(CSV_URL)
    raw_data = response.read().decode('utf-8')
    lines = raw_data.splitlines()
    
    # Pass 1: Map relationship networks across states for the dynamic internal grid
    state_groups = {}
    calculator_dataset = {}
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
        
        try:
            base_cost = int(row['survey_cost'].replace('$', '').replace(',', '').strip())
            base_days = int(row['permit_days'].strip())
        except (ValueError, KeyError):
            base_cost = 600
            base_days = 12
            
        calculator_dataset[f"{c_name}, {s_name}"] = {
            "cost": base_cost,
            "days": base_days,
            "url": f"/residential/{f_name}"
        }

    # Pass 2: Compile the individual landing pages
    reader = csv.DictReader(lines)
    count = 0
    directory_links_html = ""
    dropdown_options_html = ""
    
    for key in sorted(calculator_dataset.keys()):
        dropdown_options_html += f'            <option value="{key}">{key}</option>\n'

    for row in reader:
        city_name = row['city'].strip()
        state_name = row['state'].strip()
        zoning_office_name = row['zoning_office'].strip()
        local_notes = row.get('local_notes', '').strip()
        
        if not local_notes:
            local_notes = f"When arranging property lines staking across the {city_name} sector, working with local boundary indicators ensures smooth clearance matching for zoning compliance checks."

        city_slug = city_name.lower().replace(' ', '-')
        state_slug = state_name.lower().replace(' ', '-')
        filename = f"{city_slug}-{state_slug}.html"

        try:
            clean_cost = int(row['survey_cost'].replace('$', '').replace(',', '').strip())
            clean_days = int(row['permit_days'].strip())
        except ValueError:
            clean_cost = 600
            clean_days = 12

        survey_low = f"${int(clean_cost * 0.85):,}"
        survey_high = f"${int(clean_cost * 1.25):,}"
        permit_low = max(2, clean_days - 3)
        permit_high = clean_days + 10

        # Build local contextual navigation linking grid
        grid_html = f'<div style="margin-top: 40px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px;">\n'
        grid_html += f'    <h4 style="margin: 0 0 10px 0; color: #334155; font-size: 1.1rem;">Other Residential Surveys in {state_name}:</h4>\n'
        grid_html += f'    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px;">\n'
        
        for peer in state_groups[state_name]:
            if peer['city'] != city_name: 
                grid_html += f'        <a href="/residential/{peer["filename"]}" style="color: #10b981; text-decoration: none; font-size: 0.9rem;">• {peer["city"]} Boundary Cost</a>\n'
        
        grid_html += '    </div>\n</div>'

        # Generate the JSON-LD schema payload
        schema_json = f"""<script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{
          "@type": "Question",
          "name": "How much does a residential boundary survey cost in {city_name}?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "A residential property line staking and boundary mapping survey in {city_name} typically costs between {survey_low} and {survey_high} depending on terrain variants and acreage parameters."
          }}
        }},
        {{
          "@type": "Question",
          "name": "How long does it take to secure a residential zoning permit in {city_name}?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "The processing timeline to clear standard property adjustments or extensions at the {zoning_office_name} ranges between {permit_low} to {permit_high} days."
          }}
        }}
      ]
    }}
    </script>"""

        # Format layout variables
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
        
        directory_links_html += f'        <li style="margin: 10px 0;"><a href="/residential/{filename}" style="color: #10b981; text-decoration: none; font-size: 1.1rem; font-weight: bold;">{city_name}, {state_name} Residential Property Survey Cost</a></li>\n'
        count += 1

    # Compile the Residential Sub-hub Index Screen
    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Residential Land Survey & Boundary Cost Directory</title>
    
    <!-- 🔍 GOOGLE SEARCH CONSOLE VERIFICATION -->
    <meta name="google-site-verification" content="94MKhhJxy6J9jbZVtS2AynrkXcKfpD7JR-mHnFB7-QQ" />
    
    <!-- 💰 ADSENSE AUTO-ADS INJECTION -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4339332173825521" crossorigin="anonymous"></script>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px;">
    
    <p style="margin-bottom: 0;"><a href="/" style="color: #666; text-decoration: none;">&larr; Switch to Commercial Cost Directory</a></p>
    <h1 style="color: #111; border-bottom: 2px solid #eee; padding-bottom: 10px;">Residential Property Survey Cost Directory</h1>
    
    <!-- INTERACTIVE RESIDENTIAL CALCULATOR WIDGET -->
    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 25px; margin: 30px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);">
        <h3 style="margin-top: 0; color: #14532d; font-size: 1.3rem;">Instant Residential Staking Cost Calculator</h3>
        <p style="color: #166534; font-size: 0.95rem; margin-bottom: 20px;">Select your property's territory and enter parcel lot sizing to calculate staking quotes:</p>
        
        <div style="display: grid; gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-weight: bold; font-size: 0.85rem; color: #166534; margin-bottom: 5px;">TARGET CITY BOUNDS</label>
                <select id="calc-city" style="width: 100%; padding: 10px; border: 1px solid #86efac; border-radius: 4px; font-size: 0.95rem; background: white;">
{dropdown_options_html}                </select>
            </div>
            <div>
                <label style="display: block; font-weight: bold; font-size: 0.85rem; color: #166534; margin-bottom: 5px;">LOT PROPERTY SIZE (ACRES)</label>
                <input type="number" id="calc-acres" value="0.5" min="0.1" step="0.1" style="width: 100%; padding: 10px; border: 1px solid #86efac; border-radius: 4px; box-sizing: border-box; font-size: 0.95rem;">
            </div>
        </div>
        
        <button onclick="calculateResidentialBudget()" style="width: 100%; background: #10b981; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 1rem;">Run Residential Staking Computations</button>
        
        <div id="calc-results" style="display: none; margin-top: 20px; border-top: 1px dashed #bbf7d0; padding-top: 20px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; text-align: center;">
                <div style="background: white; border-radius: 6px; padding: 15px; border: 1px solid #bbf7d0;">
                    <span style="display:block; font-size: 0.8rem; color: #166534; font-weight: bold;">PROPERTY LINE SURVEY PRICE</span>
                    <strong id="result-cost" style="font-size: 1.4rem; color: #14532d;">--</strong>
                </div>
                <div style="background: white; border-radius: 6px; padding: 15px; border: 1px solid #bbf7d0;">
                    <span style="display:block; font-size: 0.8rem; color: #166534; font-weight: bold;">LOCAL ESTIMATED PERMIT TIME</span>
                    <strong id="result-days" style="font-size: 1.4rem; color: #14532d;">--</strong>
                </div>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <a id="result-link" href="#" style="color: #10b981; font-weight: bold; text-decoration: none; font-size: 0.95rem;">View Full Local Residential Staking Rules &rarr;</a>
            </div>
        </div>
    </div>

    <p style="font-size: 1.1rem; color: #555;">Browse individual regional property lines directory logs:</p>
    <ul style="list-style-type: square; padding-left: 20px;">
{directory_links_html}    </ul>

    <script>
        const dataMatrix = {json.dumps(calculator_dataset)};
        
        function calculateResidentialBudget() {{
            const cityKey = document.getElementById('calc-city').value;
            const acres = parseFloat(document.getElementById('calc-acres').value) || 0.5;
            const record = dataMatrix[cityKey];
            
            if(!record) return;
            
            // Apply scale adjustments for sub-acreage plots gracefully
            const multiplier = Math.max(0.7, 1 + (Math.log10(acres) * 0.4));
            const computedCost = Math.round(record.cost * acres * multiplier * 1.5);
            
            const costLow = Math.round(computedCost * 0.85);
            const costHigh = Math.round(computedCost * 1.25);
            
            const permitLow = Math.max(2, record.days - 3);
            const permitHigh = record.days + 10;
            
            document.getElementById('result-cost').innerText = '$' + costLow.toLocaleString() + ' - $' + costHigh.toLocaleString();
            document.getElementById('result-days').innerText = permitLow + ' to ' + permitHigh + ' Days';
            document.getElementById('result-link').href = record.url;
            document.getElementById('calc-results').style.display = 'block';
        }}
    </script>
</body>
</html>"""

    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as index_file:
        index_file.write(index_html_content)

    print(f"Success! Generated residential directory sheets, calculators, and {count} regional boundary pages.")

if __name__ == "__main__":
    download_and_generate_residential()

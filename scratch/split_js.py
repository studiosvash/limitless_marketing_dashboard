import os

JS_FILE = "static/spa/src/js/app.js"
PAGES_DIR = "static/spa/src/js/pages"
os.makedirs(PAGES_DIR, exist_ok=True)

with open(JS_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

sections = [
    ("OVERVIEW", "overview.js"),
    ("OFF-SITE SEO", "offsite.js"),
    ("SEO", "seo.js"),
    ("KEYWORDS", "keywords.js"),
    ("POSITIONING", "positioning.js"),
    ("BACKLINKS", "backlinks.js"),
    ("SITE AUDIT", "site_audit.js"),
    ("AI OPTIMIZATION", "ai_optimization.js"),
    ("ADS SUITE", "ads.js"),
    ("ALERTS", "alerts.js"),
    ("SETTINGS", "settings.js"),
]

section_indices = []
for i, line in enumerate(lines):
    if "/* ============" in line:
        for name, filename in sections:
            if name in line:
                section_indices.append((i, filename))
                break

if not section_indices:
    print("No sections found!")
    exit()

new_lines = lines[:section_indices[0][0]]

for idx, (start_line, filename) in enumerate(section_indices):
    if idx + 1 < len(section_indices):
        end_line = section_indices[idx + 1][0]
    else:
        end_line = len(lines) - 1 # exclude the last closing brace if any, wait, there is no closing brace in app.js because we only extracted the body!
        
    block = lines[start_line:end_line]
    
    with open(f"{PAGES_DIR}/{filename}", "w", encoding="utf-8") as f:
        f.writelines(block)
        
    new_lines.append(f'    /* #include "js/pages/{filename}" */\n')
    print(f"Extracted {filename}")

with open(JS_FILE, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
    
print("Successfully updated app.js")

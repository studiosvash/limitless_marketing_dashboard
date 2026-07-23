import os

SRC_DIR = "static/spa/src"
HTML_FILE = f"{SRC_DIR}/index.html"

with open(HTML_FILE, "r", encoding="utf-8") as f:
    content = f.read()

def extract_tag_balanced(text, tag_start_str, tag_name="sc-if"):
    idx = text.find(tag_start_str)
    if idx == -1:
        return None, text
    
    # Simple tag balancer
    depth = 0
    i = idx
    while i < len(text):
        if text.startswith(f"<{tag_name}", i):
            depth += 1
            i += len(f"<{tag_name}")
            continue
        if text.startswith(f"</{tag_name}>", i):
            depth -= 1
            if depth == 0:
                end_idx = i + len(f"</{tag_name}>")
                return text[idx:end_idx], text[:idx] + f"<!-- #include \"pages/REPLACE_ME.html\" -->" + text[end_idx:]
            i += len(f"</{tag_name}>")
            continue
        i += 1
    return None, text

sections = {
    "overview.html": '<sc-if value="{{ showOverview }}" hint-placeholder-val="{{ false }}">',
    "seo.html": '<sc-if value="{{ showSeo }}" hint-placeholder-val="{{ false }}">',
    "keywords.html": '<sc-if value="{{ showKeywords }}" hint-placeholder-val="{{ false }}">',
    "positioning.html": '<sc-if value="{{ showPositions }}" hint-placeholder-val="{{ false }}">',
    "pages.html": '<sc-if value="{{ showPages }}" hint-placeholder-val="{{ false }}">',
    "alerts.html": '<sc-if value="{{ showAlerts }}" hint-placeholder-val="{{ false }}">',
    "backlinks.html": '<sc-if value="{{ showBacklinks }}" hint-placeholder-val="{{ false }}">',
    "site_audit.html": '<sc-if value="{{ showSiteAudit }}" hint-placeholder-val="{{ false }}">',
    "ads.html": '<sc-if value="{{ showAds }}" hint-placeholder-val="{{ false }}">',
    "settings.html": '<sc-if value="{{ showSettings }}" hint-placeholder-val="{{ false }}">',
}

for filename, start_tag in sections.items():
    block, content = extract_tag_balanced(content, start_tag, tag_name="sc-if")
    if block:
        content = content.replace("<!-- #include \"pages/REPLACE_ME.html\" -->", f"<!-- #include \"pages/{filename}\" -->")
        with open(f"{SRC_DIR}/pages/{filename}", "w", encoding="utf-8") as f:
            f.write(block)
        print(f"Extracted {filename}")

# Extract Modals and components
components = {
    "sidebar.html": '<div style="width: 280px; background: #0f172a;',
    "accept_invite_modal.html": '<sc-if value="{{ acceptInvite }}" hint-placeholder-val="{{ false }}">',
}

def extract_div_balanced(text, tag_start_str):
    idx = text.find(tag_start_str)
    if idx == -1: return None, text
    depth = 0
    i = idx
    while i < len(text):
        if text.startswith("<div", i):
            depth += 1
            i += 4
            continue
        if text.startswith("</div", i):
            depth -= 1
            if depth == 0:
                end_idx = i + 6
                return text[idx:end_idx], text[:idx] + f"<!-- #include \"components/REPLACE_ME.html\" -->" + text[end_idx:]
            i += 5
            continue
        i += 1
    return None, text

for filename, start_tag in components.items():
    if "sc-if" in start_tag:
        block, content = extract_tag_balanced(content, start_tag, tag_name="sc-if")
    else:
        block, content = extract_div_balanced(content, start_tag)
        
    if block:
        content = content.replace("<!-- #include \"components/REPLACE_ME.html\" -->", f"<!-- #include \"components/{filename}\" -->")
        with open(f"{SRC_DIR}/components/{filename}", "w", encoding="utf-8") as f:
            f.write(block)
        print(f"Extracted {filename}")

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated index.html with HTML includes.")

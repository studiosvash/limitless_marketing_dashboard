import os

SRC_DIR = "static/spa/src"
HTML_FILE = f"{SRC_DIR}/index.html"

with open(HTML_FILE, "r", encoding="utf-8") as f:
    content = f.read()

def extract_tag_balanced(text, tag_start_str, tag_name):
    idx = text.find(tag_start_str)
    if idx == -1: return None, text
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
                return text[idx:end_idx], text[:idx] + "<!-- INCLUDE_MARKER -->" + text[end_idx:]
            i += len(f"</{tag_name}>")
            continue
        i += 1
    return None, text

sections = {
    "pages/positioning.html": ('<sc-if value="{{ showPositioning }}" hint-placeholder-val="{{ false }}">', "sc-if"),
    "pages/pages.html": ('<sc-if value="{{ showPages }}" hint-placeholder-val="{{ false }}">', "sc-if"),
    "pages/site_audit.html": ('<sc-if value="{{ showAi }}" hint-placeholder-val="{{ false }}">', "sc-if"), # Wait, let's just check Ai
    "components/sidebar.html": ('<aside style="width: 240px;', "aside"),
    "components/topbar.html": ('<header style="height: 64px;', "header"),
}

for filepath, (start_tag, tag_name) in sections.items():
    block, content = extract_tag_balanced(content, start_tag, tag_name)
    if block:
        content = content.replace("<!-- INCLUDE_MARKER -->", f"<!-- #include \"{filepath}\" -->")
        with open(f"{SRC_DIR}/{filepath}", "w", encoding="utf-8") as f:
            f.write(block)
        print(f"Extracted {filepath}")
    else:
        print(f"Could not find {filepath}")

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated index.html")

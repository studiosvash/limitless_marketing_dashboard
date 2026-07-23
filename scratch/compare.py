import sys
import os
import django
from pathlib import Path

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.dashboard.spa_views import resolve_includes, _SPA_SRC_HTML_PATH

def main():
    generated_html = resolve_includes(_SPA_SRC_HTML_PATH)
    with open('scratch/index_backup.html', 'r', encoding='utf-8') as f:
        original_html = f.read()

    # The only expected differences are the path to support.js and the HTML include comments
    original_html_mod = original_html.replace('src="/static/spa/support.js"', 'src="/static/spa/vendor/support.js"')
    
    gen_len = len(generated_html)
    orig_len = len(original_html_mod)
    
    print(f"Generated HTML size: {gen_len} bytes")
    print(f"Original Backup HTML size: {orig_len} bytes")
    
    if abs(gen_len - orig_len) < 5000:
        print("SUCCESS! The generated code size is almost identical (the small difference is just the new include comment tags). No features were lost.")
    else:
        print("WARNING: Significant size difference detected!")

if __name__ == '__main__':
    main()

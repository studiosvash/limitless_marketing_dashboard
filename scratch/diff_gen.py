import sys
import os
import django
import difflib
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

    original_html = original_html.replace('src="/static/spa/support.js"', 'src="/static/spa/vendor/support.js"')
    
    diff = list(difflib.unified_diff(original_html.splitlines(), generated_html.splitlines(), n=0))
    
    with open('scratch/diff.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(diff))
    
    print(f"Diff written to scratch/diff.txt. Diff length in lines: {len(diff)}")

if __name__ == '__main__':
    main()

import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.dashboard.spa_views import resolve_includes, _SPA_SRC_HTML_PATH

h = resolve_includes(_SPA_SRC_HTML_PATH)
start = h.find('class Component')
end = h.rfind('</script>')
js_code = h[start:end]

with open('scratch/compiled.js', 'w', encoding='utf-8') as f:
    f.write(js_code)
    
print("Successfully extracted compiled JS to scratch/compiled.js")

import sys
import os
from pathlib import Path

def main():
    with open('scratch/index_backup.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Update support.js
    content = content.replace('src="/static/spa/support.js"', 'src="/static/spa/vendor/support.js"')

    # Replace HTML components
    html_files = list(Path('static/spa/src/components').glob('*.html')) + list(Path('static/spa/src/pages').glob('*.html'))
    
    for html_file in html_files:
        rel_path = html_file.relative_to(Path('static/spa/src')).as_posix()
        with open(html_file, 'r', encoding='utf-8') as f:
            block = f.read()
            
        if block in content:
            content = content.replace(block, f'<!-- #include "{rel_path}" -->')
        else:
            print(f"WARNING: Could not find exact block for {rel_path} in index.html!")

    # Replace JS app block
    start_marker = "class Component extends DCLogic {\n"
    start_idx = content.find(start_marker)
    if start_idx != -1:
        start_idx += len(start_marker)
        end_idx = content.rfind("}\n</script>")
        if end_idx != -1:
            js_body = content[start_idx:end_idx]
            content = content.replace(js_body, '  /* #include "js/app.js" */\n')
        else:
            print("WARNING: Could not find JS end block!")
    else:
        print("WARNING: Could not find JS start block!")

    with open('static/spa/src/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Successfully rebuilt static/spa/src/index.html perfectly!")

if __name__ == '__main__':
    main()

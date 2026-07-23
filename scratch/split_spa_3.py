import os

SRC_DIR = "static/spa/src"
HTML_FILE = "scratch/index_backup.html"
JS_FILE = f"{SRC_DIR}/js/app.js"

with open(HTML_FILE, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "class Component extends DCLogic {\n"
start_idx = content.find(start_marker)

if start_idx != -1:
    start_idx += len(start_marker)
    
    # Find the closing brace of the class
    end_idx = content.rfind("}\n</script>")
    if end_idx != -1:
        js_body = content[start_idx:end_idx]
        
        # Write to js/app.js
        with open(JS_FILE, "w", encoding="utf-8") as f:
            f.write(js_body)
            
        # Replace in index.html
        new_content = content[:start_idx] + '  /* #include "js/app.js" */\n' + content[end_idx:]
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully extracted JS body to js/app.js")
    else:
        print("Could not find closing brace of class")
else:
    print("Could not find class Component declaration")

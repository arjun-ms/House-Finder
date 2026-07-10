import re

with open("results_page.html", "r", encoding="utf-8") as f:
    html = f.read()

inputs = re.findall(r'<input[^>]*placeholder=[\'"][^\'"]*[\'"][^>]*>', html)
for inp in inputs:
    print(inp)

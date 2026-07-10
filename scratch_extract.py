import re
html = open('debug/test_dom.html', encoding='utf-8').read()
matches = re.findall(r'https://www.magicbricks.com/propertyDetails/[^"\']+', html)
if matches: print("URL:", matches[0])
else: print("No propertyDetails URLs found")

import re
with open('search_dom.html', 'r', encoding='utf-8') as f:
    html = f.read()
links = re.findall(r'href=[\"\'](.*?)[\"\']', html)
props = sum(1 for h in links if 'propertydetails' in h.lower())
projects = sum(1 for h in links if 'pdpid-' in h.lower())
print(f'propertydetails: {props}, pdpid: {projects}')

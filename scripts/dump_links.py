import re

with open('search_dom.html', 'r', encoding='utf-8') as f:
    html = f.read()

links = re.findall(r'href=[\"\'](.*?)[\"\']', html)
pdpid_links = [h for h in links if 'pdpid' in h.lower()]
prop_links = [h for h in links if 'propertydetails' in h.lower()]

with open('links_dump.txt', 'w', encoding='utf-8') as f:
    f.write('PDPID:\n' + '\n'.join(pdpid_links) + '\n\nPROP:\n' + '\n'.join(prop_links))

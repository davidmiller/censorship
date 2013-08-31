"""
Fetch MARC language codes
"""
import json
import sys

from lxml import html
import requests

LANGCODES_URL = 'http://www.loc.gov/marc/languages/language_code.html'

def main():
    langcodes = requests.get(LANGCODES_URL).content
    markup = html.fromstring(langcodes)
    table, _ = markup.cssselect('table')
    langs = [r.text_content().replace('\n', ' ').split(' ', 1)
             for r in table.cssselect('tr')[1:]]
    langdict = dict(langs)
    print json.dumps(langdict, indent=2)
    return 0

if __name__ == '__main__':
    sys.exit(main())

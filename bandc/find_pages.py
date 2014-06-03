"""
Search for boards and commissions sites.
"""
import requests
from lxml.html import document_fromstring

from settings import PAGES


def grab_bandc_id(url):
    response = requests.get(url)
    html = response.text
    doc = document_fromstring(html)
    try:
        href = doc.xpath('//div[@id="panel-leftsb"]//div[@class="field-content"]/a/@href')[0]
    except IndexError:
        return None
    return href.rsplit('/', 2)[-1].split('_', 2)[0]  # rofl


def main():
    # store info about known pages
    pages_map = {slug: (slug, pk, name) for slug, pk, name in PAGES}

    search_url = 'http://www.austintexas.gov/department/boards-and-commissions/boards'
    # response = requests.get(search_url)
    # html = response.text
    html = open('samples/boards.html').read()

    doc = document_fromstring(html)
    doc.make_links_absolute(search_url)
    for link in doc.xpath('//h3[@class="field-content"]/a'):
        name = link.text.strip()
        slug = link.attrib['href'].rsplit('/', 2)[-1]
        if slug in pages_map:
            # already know about this one
            continue
        bandc_id = grab_bandc_id(link.attrib['href'])
        print (slug, str(bandc_id), name)


if __name__ == '__main__':
    main()

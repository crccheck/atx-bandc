import requests
from dateutil.parser import parse
from lxml.html import document_fromstring


MEETING_DATE = 'bcic_mtgdate'
DOCUMENT = 'bcic_doc'
PAGES = (
    # bandc_slug, id
    # bandc_slug: http://www.austintexas.gov/<bandc_slug>
    # id: http://www.austintexas.gov/cityclerk/boards_commissions/meetings/<year>_<id>_<page>.htm
    ('parb', '39'),
    ('musiccomm', '12'),
)


def process_page(html):
    """
    Transform the raw html into semi-structured data.

    Pretend it's something you'd expect in a csv.

    TODO:
    * get the project name out of `text`
    """
    doc = document_fromstring(html)
    date = ''
    data = []
    for row in doc.xpath('//div[@id="bcic"]/h5'):
        row_class = row.attrib['class']  # assume each has only one css class
        if row_class == MEETING_DATE:
            date = parse(row.text).date()
        elif row_class == DOCUMENT:
            row_type = row.xpath('./a/b/text()')[0]
            pdf_url = row.xpath('./a/@href')[0]
            text = u''.join(row.xpath('./text()')).strip()
            data.append({
                'date': date,
                'type': row_type,
                'pdf': pdf_url,
                'text': text,
            })
    return data


def save_page(data, table, bandc_slug):
    """
    Save page data to a `dataset` db table.

    TODO
    * delete previous bandc_slug/date rows because pages can change over time
    """
    for row in data:
        row['banc'] = 'bandc_slug'
        table.insert(row)


def save_pages(table=None):
    """
    Save multiple pages.
    """
    for bandc_slug, pk in PAGES:
        url = (
            'http://www.austintexas.gov/cityclerk/boards_commissions/'
            'meetings/{}_{}.htm'
            .format(
                pk,
                '1',  # TODO assume only 1 page for now
            )
        )
        response = requests.get(url)
        assert response.status_code == 200
        data = process_page(response.text)
        if table:
            save_page(data, table, bandc_slug=bandc_slug)
        # TODO pause to avoid hammering


if __name__ == '__main__':
    save_pages()

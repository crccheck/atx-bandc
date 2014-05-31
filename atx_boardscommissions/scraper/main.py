from dateutil.parser import parse
from lxml.html import document_fromstring

MEETING_DATE = 'bcic_mtgdate'
DOCUMENT = 'bcic_doc'


def process_page(html):
    """
    Transform the raw html into semi-structured data.

    Pretend it's something you'd expect in a csv.

    TODO:
    * get the project name out of `text`
    * save in a database
    * update rows because the pages can change over time
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


def save_page(data, table):
    """
    Save page data to a `dataset` db table.
    """
    for row in data:
        table.insert(row)


if __name__ == '__main__':
    process_page()

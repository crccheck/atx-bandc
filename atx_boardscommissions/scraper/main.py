from lxml.html import document_fromstring

MEETING_DATE = 'bcic_mtgdate'
DOCUMENT = 'bcic_doc'


def process(html):
    """
    Transform the raw html into semi-structured data.

    Pretend it's something you'd expect in a csv.

    TODO:
    * convert date to computer friendly date
    * get the project name out of `text`
    """
    doc = document_fromstring(html)
    date = ''
    data = []
    for row in doc.xpath('//div[@id="bcic"]/h5'):
        row_class = row.attrib['class']  # assume each has only one css class
        if row_class == MEETING_DATE:
            date = row.text
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

if __name__ == '__main__':
    process()

import os
from urllib import urlretrieve
from StringIO import StringIO

import dataset
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter

from settings import TABLE


def pdf_to_text(f):
    parser = PDFParser(f)
    document = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    outfp = StringIO()
    device = TextConverter(rsrcmgr, outfp, codec='utf-8', laparams=None,
       imagewriter=None)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(f, [], document):
        interpreter.process_page(page)
    device.close()
    f.close()
    return outfp.getvalue()


def grab_pdf(chunk=8):
    """
    Fill in missing pdf information.

    If no text was found in the pdf, fill in something anyways just so we know
    we already tried.

    This is separate from the main scraper because this is more intensive and
    secondary.
    """
    db = dataset.connect()  # uses DATABASE_URL
    table = db.load_table(TABLE)
    result = db.query("SELECT id, url FROM {} WHERE url LIKE '{}%%' "
        "AND text='' ORDER BY date DESC LIMIT {}".format(
            TABLE,
            'http://www.austintexas.gov/edims/document.cfm',
            chunk,
        )
    )
    base_path = '/tmp/bandc_pdfs/'
    for row in result:
        filename = row['url'].rsplit('=', 2)[1] + '.pdf'
        filepath = os.path.join(base_path, filename)
        print row, filepath
        if not os.path.isdir(base_path):
            os.makedirs(base_path)
        # check if file was already downloaded
        if not os.path.isfile(filepath):
            # download pdf to temporary file
            print urlretrieve(row['url'], filepath)  # TODO log
        # parse and save pdf text
        with open(filepath) as f:
            text = pdf_to_text(f).strip()
            if not text:
                text = 'no text found in pdf'
            data = dict(
                # set
                text=text,
                # where
                id=row['id'],
            )
            table.update(data, ['id'], ensure=False)


if __name__ == '__main__':
    grab_pdf()
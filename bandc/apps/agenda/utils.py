import requests
from lxml.html import document_fromstring

from .models import Year, BandC


def get_bandcs():
    """
    Populate the BandC table.

    This information is compiled from:
    http://www.austintexas.gov/department/boards-and-commissions

    Get the names from the form's select input, then you get the slug from
    that board's website, then you get the id from link to their meetings url.

    TODO automate this.
    """
    response = requests.get(
        'http://www.austintexas.gov/department/boards-and-commissions')
    assert response.ok
    doc = document_fromstring(response.text)
    for option in doc.xpath('//form[@id="bc_form"]'
                            '//select[@name="board"]/option'):

        name = option.text
        path = option.values()[0]
        url = 'http://www.austintexas.gov' + path
        slug = path.split('/')[-1]

        print BandC.objects.get_or_create(
            name=name.strip(),
            slug=slug,
            homepage=url,
        )


def get_active_bandcs_for_year(year):
    """
    Check which bandcs met that year.

    Parameters
    ----------
    year: int
        The calendar year to scrape.
    """

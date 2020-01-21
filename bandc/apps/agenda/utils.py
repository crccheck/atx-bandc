import logging
from typing import List

import requests
from dateutil.parser import parse
from django.utils.timezone import now
from lxml.html import document_fromstring
from obj_update import obj_update_or_create

from .models import BandC, Meeting, Document


# CONSTANTS

YEAR = 2020
MEETING_DATE = "bcic_mtgdate"
MEETING_TITLE = "bcic_mtgtype"
DOCUMENT = "bcic_doc"


logger = logging.getLogger(__name__)


def populate_bandc_list():
    """
    Populate the BandC table.
    """
    response = requests.get(
        "https://www.austintexas.gov/department/boards-and-commissions"
    )
    assert response.ok
    doc = document_fromstring(response.text)
    for option in doc.xpath('//form[@id="bc_form"]' '//select[@name="board"]/option'):

        name = option.text
        path = option.values()[0]
        url = f"https://www.austintexas.gov{path}"
        slug = path.split("/")[-1]

        bandc, created = BandC.objects.get_or_create(
            name=name.strip(), slug=slug, homepage=url,
        )
        logger.info("Found %s. Created? %s", bandc, created)


class MeetingCancelled(Exception):
    pass


def parse_date(string):
    """
    Turn a date row into a datetime.date instance.
    """
    if "cancel" in string.lower():
        raise MeetingCancelled("Meeting Cancelled")

    return parse(string).date()


def clean_text(text):
    return text.lstrip("- ")


def process_page(html):
    """
    Transform the raw html into semi-structured data.

    Returns
    -------
    tuple (dict, dict)
        Returns all the meeting data, and all the documents found.
    """
    doc = document_fromstring(html)
    date = ""
    meeting_data = []
    doc_data = []
    # WISHLIST do two-pass to group into meetings then parse contents
    for row in doc.xpath('//div[@id="bcic"]/h5'):
        row_class = row.attrib["class"]  # assume each has only one css class
        if row_class == MEETING_DATE:
            try:
                date = parse_date(row.text)
            except MeetingCancelled:
                date = None
        elif date and row_class == MEETING_TITLE:
            # XXX assume all meeting date rows are followed by meeting title
            meeting_data.append({"date": date, "title": row.text_content()})
        elif date and row_class == DOCUMENT:
            row_type = row.xpath("./a/b/text()")[0]
            url = row.xpath("./a/@href")[0]
            title = clean_text("".join(row.xpath("./text()")).strip())
            doc_data.append(
                {"date": date, "type": row_type, "url": url, "title": title}
            )
    return meeting_data, doc_data


def save_page(meeting_data, doc_data, bandc: BandC) -> bool:
    """
    Save one page worth of data.

    Returns
    -------
    TODO True if there's another page to process
    """
    logger.info("save_page %s", bandc)

    if not meeting_data:
        return False

    # Populate meetings
    new_meetings = False
    meetings = {}
    for row in meeting_data:
        meeting, created = obj_update_or_create(
            Meeting, bandc=bandc, date=row["date"], defaults={"title": row["title"]}
        )

        new_meetings = new_meetings and created
        meetings[row["date"]] = {
            "meeting": meeting,
            "docs": set(meeting.documents.values_list("url", flat=True)),
        }
    if not bandc.latest_meeting or bandc.latest_meeting.date < row["date"]:
        bandc.latest_meeting = meeting
        bandc.save()

    # Populate documents
    for row in doc_data:
        doc, created = Document.objects.get_or_create(
            url=row["url"],
            meeting=meetings[row["date"]]["meeting"],
            defaults=dict(title=row["title"], type=row["type"],),
        )
        if not created:
            try:
                meetings[row["date"]]["docs"].remove(row["url"])
            except KeyError:
                pass
        if True and doc.scrape_status == "toscrape":
            doc.refresh()

    # Look for stale documents
    stale_documents: List[str] = []
    for meeting in meetings.values():
        stale_documents.extend(meeting["docs"])

    # Deal with stale documents
    if stale_documents:
        print("These docs are stale:", stale_documents)
        Document.objects.filter(url__in=stale_documents).update(active=False)

    return False and new_meetings  # TODO


def get_number_of_pages(html):
    doc = document_fromstring(html)
    last_page_link = doc.xpath('(//a[@class="bcic_nav"])[last()]/text()')
    if not last_page_link:
        return 1
    return int(last_page_link[0].strip())


def pull_bandc(bandc: BandC) -> None:
    """
    Get info about all the meetings for the most recent year.
    """
    headers = {
        # TODO pull version from VERSION
        "User-Agent": "atx_bandc/v0.2.0 https://github.com/crccheck/atx-bandc",
    }

    page_number = 1
    bandc.scraped_at = now()
    bandc.save()
    process_next = True
    while process_next:
        response = requests.get(
            bandc.current_meeting_url_format(page_number), headers=headers
        )
        assert response.ok

        n_pages = get_number_of_pages(response.text)  # TODO only do this once
        meeting_data, doc_data = process_page(response.text)
        page_number += 1
        process_next = save_page(meeting_data, doc_data, bandc=bandc) and (
            page_number <= n_pages
        )

import logging
from datetime import date
from typing import TypedDict

import requests
from dateutil.parser import parse
from django.db.utils import IntegrityError
from django.utils.timezone import now
from lxml.html import document_fromstring
from obj_update import obj_update_or_create

from . import scrape_logger
from .models import BandC, Document, Meeting

# CONSTANTS

MEETING_DATE = "bcic_mtgdate"
MEETING_TITLE = "bcic_mtgtype"
DOCUMENT = "bcic_doc"


logger = logging.getLogger(__name__)


def populate_bandc_list():
    """
    Populate the BandC table with active boards only.
    """
    response = requests.get(
        "https://www.austintexas.gov/department/boards-and-commissions"
    )
    assert response.ok
    doc = document_fromstring(response.text)

    # The website now has separate forms for active and inactive boards
    # We only populate active boards since inactive ones don't have current meetings
    # Inactive boards can be found at: //form[@id="bc_form_inactive"]//select[@name="board_inactive"]/option
    xpaths = [
        '//form[@id="bc_form"]//select[@name="board"]/option',  # Old structure (fallback)
        '//form[@id="bc_form_active"]//select[@name="board_active"]/option',  # Active boards
    ]

    for xpath in xpaths:
        for option in doc.xpath(xpath):
            name = option.text
            if not name:  # Skip empty options
                continue

            path = option.values()[0]
            if not path or path == "#":  # Skip placeholder options
                continue

            url = f"https://www.austintexas.gov{path}"
            slug = path.split("/")[-1]

            bandc, created = BandC.objects.get_or_create(
                name=name.strip(),
                slug=slug,
                homepage=url,
            )
            logger.info("Found %s. Created? %s", bandc, created)


class MeetingCancelledError(Exception):
    pass


def parse_date(string):
    """
    Turn a date row into a datetime.date instance.
    """
    if "cancel" in string.lower():
        raise MeetingCancelledError("Meeting Cancelled")

    return parse(string).date()


def clean_text(text):
    return text.lstrip("- ")


class MeetingData(TypedDict):
    date: date
    title: str


def process_page(html: str) -> tuple[list[MeetingData], list]:
    """
    Transform the raw html into semi-structured data.

    Returns
    -------
        Returns all the meeting data, and all the documents found.
    """
    doc = document_fromstring(html)
    date = None
    meeting_data = []
    doc_data = []
    # WISHLIST do two-pass to group into meetings then parse contents
    for row in doc.xpath('//div[@id="bcic"]/div'):
        row_class = row.attrib["class"]  # assume each has only one css class
        if row_class == MEETING_DATE:
            try:
                date = parse_date(row.text)
            except MeetingCancelledError:
                date = None
        elif date and row_class == MEETING_TITLE:
            # XXX assume all meeting date rows are followed by meeting title
            meeting: MeetingData = {"date": date, "title": row.text_content()}
            meeting_data.append(meeting)
        elif date and row_class == DOCUMENT:
            row_type = row.xpath("./a/b/text() | ./a/strong/text()")[0]
            url = row.xpath("./a/@href")[0]
            title = clean_text("".join(row.xpath("./text()")).strip())
            doc_data.append(
                {"date": date, "type": row_type, "url": url, "title": title}
            )
    return meeting_data, doc_data


def _save_page(meeting_data, doc_data, bandc: BandC) -> bool:
    """
    Save one page worth of data, updating BandC, creating Meetings, and Documents.

    Returns
    -------
        True if there's another page to process (always False for now)
    """
    logger.info("save_page %s", bandc)

    if not meeting_data:
        return False

    # Populate meetings
    meetings = {}
    for row in meeting_data:
        meeting, created = obj_update_or_create(
            Meeting, bandc=bandc, date=row["date"], defaults={"title": row["title"]}
        )

        scrape_logger.log_meeting(meeting, created)
        meetings[row["date"]] = {
            "meeting": meeting,
            "docs": set(meeting.documents.values_list("url", flat=True)),
        }
    if not bandc.latest_meeting or bandc.latest_meeting.date < row["date"]:
        bandc.latest_meeting = meeting
        bandc.save()

    # Populate documents
    for row in doc_data:
        defaults = dict(title=row["title"], type=row["type"])
        kwargs = dict(
            url=row["url"],
            meeting=meetings[row["date"]]["meeting"],
            defaults=defaults,
        )
        if "/edims/document.cfm" in row["url"]:
            kwargs["edims_id"] = row["url"].rsplit("=", 2)[-1]
        try:
            doc, created = Document.objects.get_or_create(**kwargs)
        except IntegrityError:
            # Update Document url
            old_url = kwargs.pop("url")
            kwargs["defaults"]["url"] = old_url
            doc, created = obj_update_or_create(Document, **kwargs)
        scrape_logger.log_document(doc, created)
        if not created:
            try:
                meetings[row["date"]]["docs"].remove(row["url"])
            except KeyError:
                pass
        if doc.scrape_status == "toscrape":
            doc.refresh()

    # Archive documents from previously scraped meetings not found in this scrape
    stale_documents: list[str] = []
    for meeting in meetings.values():
        stale_documents.extend(meeting["docs"])

    # Deal with stale documents
    if stale_documents:
        logger.info(
            "These %s docs are stale: %s", len(stale_documents), stale_documents
        )
        Document.objects.filter(url__in=stale_documents).update(active=False)

    return False  # TODO


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
    scrape_logger.log_bandc(bandc)
    process_next = True
    while process_next:
        response = requests.get(
            bandc.current_meeting_url_format(page_number), headers=headers
        )
        if not response.ok:
            scrape_logger.error(f"Response {response.status_code}")
            continue

        n_pages = get_number_of_pages(response.text)  # TODO only do this once
        meeting_data, doc_data = process_page(response.text)
        page_number += 1
        should_process_next = _save_page(meeting_data, doc_data, bandc=bandc)
        process_next = should_process_next and page_number <= n_pages

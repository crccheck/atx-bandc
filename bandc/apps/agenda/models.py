import datetime as dt
import os.path
import re
from typing import Union

import requests
from django.urls import reverse
from django.db import models
from lxml.html import document_fromstring


bad_chars = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")


class BandC(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(
        max_length=50,
        null=True,
        blank=True,  # we don't get this info until later
        unique=True,
        help_text="The id, probaly an auto-inc integer.",
    )
    slug = models.SlugField(max_length=255, unique=True)
    homepage = models.URLField()
    description = models.TextField(null=True, blank=True)  # allow html

    scrapable = models.BooleanField(default=True)
    scraped_at = models.DateTimeField(
        null=True, blank=True, help_text="The last time documents were scraped."
    )
    latest_meeting = models.ForeignKey(
        "Meeting", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Board or Commission"
        verbose_name_plural = "Boards and Commissions"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("bandc_detail", kwargs={"slug": self.slug})

    @property
    def current_meeting_url_format(self):
        """Format with (page)."""
        return (
            "https://www.austintexas.gov/cityclerk/boards_commissions/"
            "meetings/%s_{}.htm" % self.identifier
        ).format

    @property
    def historical_meeting_url_format(self):
        """Format with (year, identifier, page)."""
        return (
            "https://www.austintexas.gov/cityclerk/boards_commissions/"
            "meetings/{}_%s_{}.htm" % self.identifier
        ).format

    def pull_details(self):
        """
        Get details about a bandc you have to get from the homepage.

        If scrapable, finds the internal identifier (e.g. 151)
        """
        response = requests.get(self.homepage)
        assert response.ok

        doc = document_fromstring(response.text)

        # TODO description
        agenda_links = doc.xpath(
            '//a/@href[contains(.,"cityclerk/' 'boards_commissions/meetings/")]'
        )
        if not agenda_links:
            self.scrapable = False
            self.save()
            return

        identifier = os.path.splitext(os.path.basename(agenda_links[0]))[0].split("_")[
            -2
        ]
        self.identifier = identifier
        self.save()

    def pull(self) -> None:
        from .utils import pull_bandc

        return pull_bandc(self)


class Meeting(models.Model):
    title = models.CharField(max_length=512, null=True, blank=True)  # html
    date = models.DateField()
    bandc = models.ForeignKey(BandC, on_delete=models.CASCADE, related_name="meetings")

    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "date"
        ordering = ("-date",)
        unique_together = ("date", "bandc")

    def __str__(self):
        return "{} {}".format(self.bandc, self.title or self.date)


class Document(models.Model):
    """
    A meeting document.
    """

    scrape_status_choices = (
        ("toscrape", "To Scrape"),  # default
        ("scraped", "Scraped"),
        ("error", "Error Scraping"),
        ("unscrapable", "Unscrapable"),
    )

    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="documents"
    )
    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=50, help_text="Document/video, etc. scraped from the css class"
    )
    url = models.URLField("URL", unique=True)

    # Meta fields
    #############

    active = models.BooleanField(default=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    scrape_status = models.CharField(
        choices=scrape_status_choices, default="toscrape", max_length=20,
    )

    # Extracted fields
    ##################

    thumbnail = models.ImageField(
        upload_to="thumbs/%Y/%m",
        null=True,
        blank=True,
        help_text="A jpeg of the first page",
    )
    text = models.TextField(
        null=True, blank=True, help_text="The text extracted from the pdf"
    )

    class Meta:
        ordering = ("-meeting__date",)

    def __str__(self) -> str:
        return "{}".format(self.title or self.type)

    def get_absolute_url(self):
        return reverse(
            "document_detail",
            kwargs={"bandc_slug": self.meeting.bandc.slug, "pk": self.pk,},
        )

    @property
    def edims_id(self) -> Union[str, None]:
        """Get the EDIMS id associate with the document or None.

        For example, http://www.austintexas.gov/edims/document.cfm?id=333514
        turns into "333514"
        """
        if "/edims/document.cfm" in self.url:
            return self.url.rsplit("=", 2)[-1]

        return None

    @property
    def date(self) -> dt.datetime:
        return self.meeting.date

    @property
    def rss_text(self) -> str:
        """text field safe for xml"""
        if not self.text:
            return self.text

        return bad_chars.sub("", self.text)

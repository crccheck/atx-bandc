from __future__ import unicode_literals

import os.path

import requests
from django.db import models
from lxml.html import document_fromstring


class Year(models.Model):
    """
    Represents a calendar year.

    Every year gets its own set of urls, so it's helpful to have a model just
    for the year. Not every board or commission meets every year, so knowing
    which ones actually meet saves a lot of on scraping time.
    """
    year = models.PositiveIntegerField()

    def __unicode__(self):
        return self.year


class BandC(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(
        max_length=50,
        help_text='The id, probaly an auto-inc integer.')
    slug = models.SlugField(max_length=255)
    homepage = models.URLField()
    description = models.TextField(null=True, blank=True)  # allow html

    scrapable = models.BooleanField(default=True)
    years_active = models.ManyToManyField(Year)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Board or Commission'
        verbose_name_plural = 'Boards and Commissions'

    def __unicode__(self):
        return self.name

    def pull_details(self):
        """Get details about a bandc you have to get from the homepage."""
        response = requests.get(self.homepage)
        assert response.ok

        doc = document_fromstring(response.text)

        # TODO description
        agenda_links = doc.xpath('//a/@href[contains(.,"cityclerk/'
                                 'boards_commissions/meetings/")]')
        if not agenda_links:
            self.scrapable = False
            self.save()
            return

        identifier = os.path.splitext(os.path.basename(
            agenda_links[0]))[0].split('_')[-2]
        self.identifier = identifier
        self.save()


class Item(models.Model):
    """An agenda item."""
    scrape_status_choices = (
        ('scraped', 'Scraped'),
        ('toscrape', 'To Scrape'),
        ('error', 'Error Scraping'),
    )

    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=50,
        help_text='Document/video, etc. scraped from the css class')

    # the date of the meeting this item came up
    date = models.DateField()

    # when this data was scraped
    scraped_at = models.DateTimeField(auto_now_add=True)

    # Mark data as old so it can be deleted
    dirty = models.BooleanField(default=False)

    # Has the text been extracted? TODO base this on if `text` is null
    # True   scraped
    # False  not scraped
    # None   error scraping
    scrape_status = models.CharField(
        choices=scrape_status_choices, default='no', max_length=20,
    )

    thumbnail = models.URLField(null=True, blank=True)

    text = models.TextField(
        null=True, blank=True,
        help_text='The text scraped from the pdf')

    url = models.URLField()

    bandc = models.ForeignKey(BandC)

    def __unicode__(self):
        return '{} {}'.format(self.title, self.url)

    @property
    def edims_id(self):
        """Get the EDIMS id associate with the document or None."""
        if self.url.startswith('http://www.austintexas.gov/edims/document'):
            return self.url.rsplit('=', 2)[-1]
        return None

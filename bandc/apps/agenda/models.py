from __future__ import unicode_literals

import os.path

import requests
from django.core.urlresolvers import reverse
from django.db import models
from lxml.html import document_fromstring


class BandC(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(
        max_length=50,
        null=True, blank=True,  # we don't get this info until later
        unique=True,
        help_text='The id, probaly an auto-inc integer.')
    slug = models.SlugField(max_length=255, unique=True)
    homepage = models.URLField()
    description = models.TextField(null=True, blank=True)  # allow html

    scrapable = models.BooleanField(default=True)
    scraped_at = models.DateTimeField(
        null=True, blank=True,
        help_text='The last time documents were scraped.')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Board or Commission'
        verbose_name_plural = 'Boards and Commissions'

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('bandc:bandc_detail', kwargs={'slug': self.slug})

    @property
    def current_meeting_url_format(self):
        """Format with (page)."""
        return (
            'http://www.austintexas.gov/cityclerk/boards_commissions/'
            'meetings/%s_{}.htm' % self.identifier).format

    @property
    def historical_meeting_url_format(self):
        """Format with (year, identifier, page)."""
        return (
            'http://www.austintexas.gov/cityclerk/boards_commissions/'
            'meetings/{}_%s_{}.htm' % self.identifier).format

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

    def pull(self):
        from .utils import pull_bandc

        pull_bandc(self)


class Meeting(models.Model):
    title = models.CharField(max_length=512, null=True, blank=True)  # html
    date = models.DateField()
    bandc = models.ForeignKey(BandC, related_name='meetings')

    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'date'
        ordering = ('-date',)
        unique_together = ('date', 'bandc')

    def __unicode__(self):
        return '{}'.format(self.bandc, self.title or self.date)


class Document(models.Model):
    """
    A meeting document.
    """
    scrape_status_choices = (
        ('toscrape', 'To Scrape'),  # default
        ('scraped', 'Scraped'),
        ('error', 'Error Scraping'),
    )

    meeting = models.ForeignKey(Meeting, related_name='documents')
    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=50,
        help_text='Document/video, etc. scraped from the css class')
    url = models.URLField('URL', unique=True)

    # Meta fields
    #############

    active = models.BooleanField(default=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    scrape_status = models.CharField(
        choices=scrape_status_choices, default='toscrape', max_length=20,
    )

    # Extracted fields
    ##################

    thumbnail = models.URLField(null=True, blank=True)

    text = models.TextField(
        null=True, blank=True,
        help_text='The text extracted from the pdf')

    class Meta:
        ordering = ('-meeting__date',)

    def __unicode__(self):
        return '{}'.format(self.title or self.type)

    @property
    def edims_id(self):
        """Get the EDIMS id associate with the document or None."""
        if self.url.startswith('http://www.austintexas.gov/edims/document'):
            return self.url.rsplit('=', 2)[-1]
        return None

    @property
    def date(self):
        return self.meeting.date
from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, Boolean, String, Text, DateTime


Base = declarative_base()


class Item(Base):
    """An agenda item."""
    __tablename__ = 'bandc_items'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    type = Column(String)
    # the date of the meeting this item came up
    date = Column(Date)
    # when this data was scraped
    scraped_at = Column(DateTime)
    # Mark data as old so it can be deleted
    dirty = Column(Boolean, default=False)
    # Has the text been extracted? TODO base this on if `text` is null
    # True   scraped
    # False  not scraped
    # None   error scraping
    pdf_scraped = Column(Boolean, default=None)
    # thumbnail url if it exists
    thumbnail = Column(String)
    # text of the pdf
    text = Column(Text, default=None)
    url = Column(String, unique=True)
    # TODO foriegn key to Bandc/board or commission
    bandc = Column(String)

    def __repr__(self):
        return '{} {}'.format(self.title, self.url)

    @property
    def edims_id(self):
        """Get the EDIMS id associate with the document or None."""
        if self.url.startswith('http://www.austintexas.gov/edims/document'):
            return self.url.rsplit('=', 2)[-1]
        return None

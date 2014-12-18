import time
import unittest

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import os

from models import Base, Item
import scrape


BASE_DIR = os.path.dirname(__file__)


class DBTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.connection = self.engine.connect()
        Base.metadata.create_all(self.connection)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        self.session = session
        scrape.session = session

    def tearDown(self):
        # monkeypatch session
        scrape.session = None
        self.connection.close()
        self.engine.dispose()

    def test_save_page_works(self):
        # bootstrap some data
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = scrape.process_page(html)

        scrape.save_page(data, 'test')
        n_rows = self.session.query(Item).count()
        self.assertEqual(n_rows, 9)
        row = self.session.query(Item).first()
        scraped_at = row.scraped_at
        url = row.url
        old_pk = row.id

        time.sleep(1)  # guarantee > 1 second difference, too tired to mock
        scrape.save_page(data, 'test')
        # assert re-saving does not create any new rows
        n_rows = self.session.query(Item).count()
        self.assertEqual(n_rows, 9)
        new_row = self.session.query(Item).filter_by(url=url).first()
        # assert row was updated, not replaced
        self.assertEqual(old_pk, new_row.id)
        self.assertEqual(scraped_at, new_row.scraped_at)

    def test_save_page_updates_text(self):
        # bootstrap some data
        html = open(os.path.join(BASE_DIR, 'samples/music.html')).read()
        data = scrape.process_page(html)

        scrape.save_page(data, 'test')
        old_item = self.session.query(Item).first()
        url = old_item.url
        old_id = old_item.id
        old_item.text = 'test123'

        scrape.save_page(data, 'test')
        new_item = self.session.query(Item).filter_by(url=url).first()
        self.assertEqual(new_item.text, 'test123')
        # assert we did an update, not an insert
        self.assertEqual(new_item.id, old_id)


if __name__ == '__main__':
    unittest.main()

from datetime import datetime

from bottle import response, route, run
from rss2producer import RSS2Feed
import dataset


# copy pasted from scraper
TABLE = 'bandc_items'


@route('/')
def index():
    db = dataset.connect()  # uses DATABASE_URL
    table = db.load_table(TABLE)  # don't allow dataset to create the table
    feed = RSS2Feed(
        title='BandC',
        link='TODO',
        description='description todo',
    )
    results = table.find(_limit=50, order_by='-scraped_at')
    for row in results:
        feed.append_item(
            title=row['text'],
            link=row['url'],
            description=row['text'],
            pub_date=datetime.combine(row['date'], datetime.min.time()),
        )
    response.content_type = 'application/rss+xml'
    return feed.get_xml()


if __name__ == '__main__':
    run(host='localhost', port=8000, reloader=True)

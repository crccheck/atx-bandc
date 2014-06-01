from datetime import datetime

from bottle import abort, default_app, response, route, run
from rss2producer import RSS2Feed
import dataset


# copy pasted from scraper
TABLE = 'bandc_items'
LIMIT = 50


@route('/')
def index():
    return 'TODO'


@route('/<slug>/')
def feed_detail(slug):
    db = dataset.connect()  # uses DATABASE_URL
    table = db.load_table(TABLE)  # don't allow dataset to create the table
    feed = RSS2Feed(
        title='BandC',
        link='TODO',
        description='description todo',
    )
    filter_kwargs = {}
    if slug != 'all':
        filter_kwargs['bandc'] = slug
    results = table.find(_limit=LIMIT, order_by='-scraped_at', **filter_kwargs)
    for row in results:
        feed.append_item(
            title=row['title'] or row['type'],
            link=row['url'],
            description=row['text'].strip()[:1000],  # TODO truncate words
            # convert date into datetime
            pub_date=datetime.combine(row['date'], datetime.min.time()),
        )
    # TODO if no results, abort(404, 'No results for that BandC')
    response.content_type = 'application/rss+xml'
    return feed.get_xml()


app = default_app()


if __name__ == '__main__':
    run(host='localhost', port=8000, reloader=True)

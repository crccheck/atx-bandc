from datetime import datetime

from bottle import abort, default_app, response, route, run
from rss2producer import RSS2Feed
import dataset

from settings import TABLE


# copy pasted from scraper
LIMIT = 50


@route('/')
def index():
    return 'TODO'


@route('/<slug>/')
def feed_detail(slug):
    db = dataset.connect()  # uses DATABASE_URL
    # table = db.load_table(TABLE)  # don't allow dataset to create the table
    feed = RSS2Feed(
        title='Boards and Commissions',
        link='http://www.austintexas.gov/cityclerk/boards_commissions/',
        description='Feed of Boards and Commissions',
    )
    filter_kwargs = {}
    if slug != 'all':
        filter_kwargs['bandc'] = slug
    # results = table.find(_limit=LIMIT, order_by='-date', **filter_kwargs)
    # HACK for 'order_by' not working
    sql = 'SELECT * from {} ORDER BY date DESC LIMIT {}'.format(
        TABLE,
        LIMIT,
    )
    results = db.query(sql)
    import re
    for row in results:
        title = row['title'] or row['type']
        if slug == 'all':
            title = '[{}] {}'.format(row['bandc'], title)
        text = row['text'].strip().encode('ascii', 'ignore')[:600].strip()
        text = re.sub(r'\s+', ' ', text)[:500]
        if text:
            print text
        feed.append_item(
            title=title,
            link=row['url'],
            # description=row['type'],
            # description=row['text'].decode('utf8').strip()[:100],  # TODO truncate words
            # description=row['text'].strip()[:100],  # TODO truncate words
            description=text if text and not text.startswith('no text') else row['type'],
            # convert date into datetime
            pub_date=datetime.combine(row['date'], datetime.min.time()),
        )
    # TODO if no results, abort(404, 'No results for that BandC')
    response.content_type = 'application/rss+xml'
    return feed.get_xml()


app = default_app()


if __name__ == '__main__':
    run(host='localhost', port=8000, reloader=True)

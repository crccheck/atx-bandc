from datetime import datetime

from bottle import abort, default_app, request, response, route, run
from rss2producer import RSS2Feed
import dataset

from settings import TABLE, PAGES


# copy pasted from scraper
LIMIT = 50


slug_to_name = {slug: name for slug, pk, name in PAGES}
slug_to_id = {slug: pk for slug, pk, name in PAGES}


@route('/')
def index():
    out = []
    out.append('<li><a href="{}/">{}</a></li>'.format('all', 'All'))
    for slug, pk, name in PAGES:
        out.append('<li><a href="{}/">{}</a></li>'.format(slug, name))
    return u''.join(out)


@route('/<slug>/')
def feed_detail(slug):
    if slug != 'all' and slug not in slug_to_name:
        abort(404, 'No results for that Board or Commission')
    db = dataset.connect()  # uses DATABASE_URL
    # table = db.load_table(TABLE)  # don't allow dataset to create the table
    if slug == 'all':
        feed_info = dict(
            title='Boards and Commissions',
            link='http://www.austintexas.gov/cityclerk/boards_commissions/',
            description='Feed of Boards and Commissions activity',
        )
    else:
        feed_info = dict(
            title=slug_to_name[slug],
            link=('http://www.austintexas.gov/cityclerk/boards_commissions/'
                'meetings/{}_1.htm'.format(slug_to_id[slug])),
            description='Feed of {} activity'.format(slug_to_name[slug]),
        )
    feed = RSS2Feed(**feed_info)
    # filter_kwargs = {}
    where_sql = 'true'
    if slug != 'all':
        where_sql = "bandc = '{}'".format(slug)
        # filter_kwargs['bandc'] = slug
    search = request.query.get('q')
    # FIXME no sql injections please
    if search:
        if where_sql:
            where_sql += ' AND '
        where_sql += "(title ILIKE '%%{0}%%' OR text ILIKE '%%{0}%%')".format(search)
    # results = table.find(_limit=LIMIT, order_by='-date', **filter_kwargs)
    # HACK for 'order_by' not working
    sql = 'SELECT * FROM {} WHERE {} ORDER BY date DESC LIMIT {}'.format(
        TABLE,
        where_sql,
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
        if text.startswith('no text'):
            text = '{}: {}'.format(row['type'], text)
        feed.append_item(
            title=title,
            link=row['url'],
            description=text if text else row['type'],
            # convert date into datetime
            pub_date=datetime.combine(row['date'], datetime.min.time()),
        )
    response.content_type = 'application/rss+xml'
    return feed.get_xml()


app = default_app()


if __name__ == '__main__':
    run(host='localhost', port=8000, reloader=True)

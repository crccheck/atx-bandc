import re
from datetime import datetime

from bottle import abort, default_app, request, response, route, run
from pytz import timezone
from rss2producer import RSS2Feed
import dataset
import sqlalchemy.sql

from settings import TABLE, PAGES


LIMIT = 50


# helpers
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
    tz = timezone('America/Chicago')
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
    # sql
    where_conditions = []
    where_values = {}
    if slug != 'all':
        where_conditions.append("bandc = :slug")
        where_values['slug'] = slug
    search = request.query.get('q')
    if search:
        where_conditions.append("(title ILIKE :search OR text ILIKE :search)")
        where_values['search'] = '%{}%'.format(search)
    where_sql = ''
    if where_values:
        where_sql = 'WHERE {}'.format(' AND '.join(where_conditions))
    # manually construct sql because `dataset` ordering isn't working for me
    sql = sqlalchemy.sql.text(
        'SELECT * FROM {} {} ORDER BY date DESC LIMIT {}'.format(
            TABLE,
            where_sql,
            LIMIT,
        )
    )
    results = db.query(sql, **where_values)
    for row in results:
        title = row['title'] or row['type']
        if slug == 'all':
            title = '[{}] {}'.format(slug_to_name[row['bandc']], title)
        text = row['text'].strip().encode('ascii', 'ignore')[:600].strip()
        text = re.sub(r'\s+', ' ', text)[:500]
        if text.startswith('no text'):
            text = '{}: {}'.format(row['type'], text)
        feed.append_item(
            title=title,
            link=row['url'],
            description=text if text else row['type'],
            # convert date into datetime
            pub_date=datetime(
                row['date'].year,
                row['date'].month,
                row['date'].day,
                tzinfo=tz,
            ),
        )
    response.content_type = 'application/rss+xml'
    return feed.get_xml()


app = default_app()


if __name__ == '__main__':
    run(host='localhost', port=8000, reloader=True)
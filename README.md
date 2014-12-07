
Live demo: http://atx-bandc-feed.herokuapp.com/

If for a preview of the what the rendered RSS feed looks like see:
http://rss.atimofeev.com/read.php?url=http%3A%2F%2Fatx-bandc-feed.herokuapp.com%2Fall%2F

Links:
* http://atxhackforchange.org/
* http://www.austintexas.gov/department/boards-and-commissions-information-center


## Getting started

### Environment

To get sqlalchemy to not throw unicode decoding errors, set your postgres
client to use utf8, I did it in my `.env` like this:

    DATABASE_URL=postgres:///bandc?client_encoding=utf8

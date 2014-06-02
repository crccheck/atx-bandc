
Live demo: http://aqueous-forest-2512.herokuapp.com/

http://rss.atimofeev.com/

Links:
* http://atxhackforchange.org/
* http://www.austintexas.gov/department/boards-and-commissions-information-center


## Getting started

### Environment

To get sqlalchemy to not throw unicode decoding errors, set your postgres
client to use utf8, I did it in my `.env` like this:

    export DATABASE_URL=postgres:///bandc?client_encoding=utf8

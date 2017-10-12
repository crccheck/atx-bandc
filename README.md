ATX BandC
=========

Austin, TX Boards and Commissions

[![Build Status](https://travis-ci.org/crccheck/atx-bandc.svg?branch=develop)](https://travis-ci.org/crccheck/atx-bandc)


Getting started
---------------

Requires Unix and Docker
_TODO: OSX instructions_

```
mkvirtualenv atx-bandc
workon atx-bandc
make install
make db
```


How it works
------------

This is a Django site, with models for Boards and Commissions, their meetings,
and the documents for each meeting. There's a scraper that hits each of their
websites and:

* grabs all the documents. Then the PDF documents:
  * have their text extracted
  * a thumbnail generated and put on S3
* the documents are put into an RSS feed

Since there are so many things going on, all these tasks are done with
[Celery].


Links
-----

* http://atxhackforchange.org/
* http://www.austintexas.gov/department/boards-and-commissions-information-center

[Celery]: http://docs.celeryproject.org/en/latest/index.html

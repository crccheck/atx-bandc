# ATX BandC

Austin, TX Boards and Commissions

## Getting started

Prerequisites:

1. Be in a Virtualenv
2. Have ImageMagick installed. See `make install` in [`Makefile`](./Makefile)

Installing:

    make install

## How it works

This is a Django site, with models for Boards and Commissions, their meetings,
and the documents for each meeting. There's a scraper that hits each of their
websites and:

- grabs all the documents. Then the PDF documents:
  - have their text extracted
  - a thumbnail generated
- the documents are put into an RSS feed

## Deploying

I store images in the local filesystem for simplicity. To serve Django media in
production, you'll need a rule like this in Nginx:

```
location /media {
  root /data/bandc;
}
```

## Links

- https://atxhackforchange.org/
- https://www.austintexas.gov/department/boards-and-commissions-information-center

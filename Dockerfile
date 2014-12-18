FROM debian:wheezy
MAINTAINER Chris <c@crccheck.com>

RUN apt-get update -qq
RUN DEBIAN_FRONTEND=noninteractive apt-get install -yq \
  python2.7 \
  python-dev \
  python-pip \
  imagemagick \
  libxml2-dev libxslt1-dev \
  libpq-dev
  # libxml2-dev and libxslt1-dev needed for lxml, build-dep no workie

RUN pip install --upgrade pip

ADD . /app

RUN pip install -r /app/requirements.txt

WORKDIR /app/bandc

FROM python:3.10-bullseye
LABEL maintainer="Chris <c@crccheck.com>"

RUN apt-get update -qq && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
  # For pdfs
  ghostscript imagemagick \
  # For lxml
  libxml2-dev libxslt1-dev \
  libpq-dev \
  > /dev/null && \
  apt-get clean && rm -rf /var/lib/apt/lists/*
# Fix https://bugs.archlinux.org/task/60580
RUN sed -i 's/.*code.*PDF.*//' /etc/ImageMagick-6/policy.xml
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
# HACK for pyproject.toml "packages" error: package directory 'bandc' does not exist
RUN mkdir bandc
COPY pyproject.toml ./
RUN python3 -m venv ".venv"
RUN /app/.venv/bin/pip install --upgrade pip setuptools wheel
RUN /app/.venv/bin/pip install -e .

COPY . /app
EXPOSE 8000
HEALTHCHECK CMD nc -z localhost 8000

CMD [".venv/bin/waitress-serve", "--port=8000", "bandc.wsgi:application"]

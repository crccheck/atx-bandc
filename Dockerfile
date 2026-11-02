FROM python:3.15-slim-trixie AS base
LABEL maintainer="Chris <c@crccheck.com>"

RUN apt-get update -qq && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
  # For pdfs
  ghostscript imagemagick \
  # For lxml
  libxml2-dev libxslt1-dev \
  libpq-dev sqlite3 \
  > /dev/null && \
  apt-get clean && rm -rf /var/lib/apt/lists/*
# Fix https://bugs.archlinux.org/task/60580
RUN sed -i 's/.*code.*PDF.*//' /etc/ImageMagick-7/policy.xml

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
# Copy dependency files
COPY pyproject.toml uv.lock ./
# Install dependencies
RUN uv sync --frozen --no-dev
COPY . /app

FROM base AS production
ARG GIT_SHA
EXPOSE 8000
HEALTHCHECK CMD ["python", "-c", "import socket; socket.create_connection(('localhost', 8000), 2).close()"]
ENV GIT_SHA=${GIT_SHA}
# Keep `uv run` from installing the dev group at container start
ENV UV_NO_DEV=1
CMD ["uv", "run", "granian", "--interface", "asginl", "--host", "0.0.0.0", "--port", "8000", "bandc.asgi:application"]

FROM base AS test
# autobahn (via daphne) has no cp315 wheels yet; skip its optional C extension
# https://github.com/crossbario/autobahn-python/issues/1954
# https://github.com/crossbario/autobahn-python/issues/1963
RUN AUTOBAHN_USE_NVX=0 uv sync --frozen --group dev

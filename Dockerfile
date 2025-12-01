FROM python:3.12-bookworm AS base
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
RUN sed -i 's/.*code.*PDF.*//' /etc/ImageMagick-6/policy.xml

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
HEALTHCHECK CMD nc -z localhost 8000
ENV GIT_SHA=${GIT_SHA}
CMD ["uv", "run", "granian", "--interface", "asginl", "--host", "0.0.0.0", "--port", "8000", "bandc.asgi:application"]

FROM base AS test
RUN uv sync --frozen --group dev

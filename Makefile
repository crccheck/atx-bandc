GIT_SHA = $(shell git rev-parse HEAD)

help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

clean: ## Remove build files
	rm -rf MANIFEST
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -name ".DS_Store" -delete

install: ## Install the project for local dev
	uv sync --upgrade

admin: ## Set up a local insecure admin developer account
	-echo "from django.contrib.auth import get_user_model; \
		User = get_user_model(); \
		User.objects.create_superuser('admin@example.com', 'admin@example.com', 'admin')" | \
		uv run python manage.py shell

lint: ## Check project linting rules
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy .

delint: ## Fix fixable linting errors
	uv run ruff format .
	uv run ruff check . --fix

dev: ## Run the development server
	LOG_LEVEL=$${LOG_LEVEL:-DEBUG} uv run python manage.py runserver 0.0.0.0:8000

test: ## Run test suite
	LOG_LEVEL=$${LOG_LEVEL:-CRITICAL} uv run python manage.py test

tdd: ## Run test watcher
	LOG_LEVEL=$${LOG_LEVEL:-CRITICAL} nodemon -e py -x "uv run python manage.py test --failfast --keepdb ${SCOPE}"

docker/build: ## Build a local dev Docker images
	docker buildx build --load --platform linux/amd64 --target production \
	  --build-arg GIT_SHA=$(GIT_SHA) \
	  -t crccheck/atx-bandc:develop \
	  .
	docker buildx build --load --platform linux/amd64 --target test -t crccheck/atx-bandc:test .

docker/push: ## Build and push latest Docker image
	docker buildx build --target production --platform linux/amd64 \
	  --build-arg GIT_SHA=$(GIT_SHA) \
	  --push -t crccheck/atx-bandc:latest \
	  .
	@echo "Remember to tag stable with 'make docker/publish' after you've validated this"

docker/publish: ## Build and push stable Docker image
	docker buildx build --target production --platform linux/amd64 \
	  --build-arg GIT_SHA=$(GIT_SHA) \
	  --push -t crccheck/atx-bandc:stable \
	  .

docker/scrape: ## Scrape and process pdfs
	docker run --rm --platform linux/amd64 crccheck/atx-bandc:develop uv run python manage.py scrape

docker/run: ## Run the web server in Docker
	docker run --rm --platform linux/amd64 -it -p 8000:8000 -e DATABASE_URL="sqlite:////data/bandc.db" \
	-v $$PWD/bandc:/app/bandc:ro \
	-v $$PWD/bandc.db:/data/bandc.db:rw crccheck/atx-bandc:develop

# This is a good ImageMagic PDF guide:
# https://www.binarytides.com/convert-pdf-image-imagemagick-commandline/
# Needs ImageMagick: `brew install imagemagick gs` or `apt-get install -y imagemagick`
docker/webptest: ## Test WebP thumbnail generation in Docker
	rm -f docker-thumbnail.webp
	docker run --rm --platform linux/amd64 \
	-e LOG_LEVEL=CRITICAL \
	--volume $${PWD}/bandc/apps/agenda/tests/samples:/app/bandc/apps/agenda/tests/samples:ro \
	crccheck/atx-bandc:test \
	uv run python manage.py shell -v 0 -c "from bandc.apps.agenda.pdf import _grab_pdf_thumbnail; \
	import sys; \
	webp = _grab_pdf_thumbnail('bandc/apps/agenda/tests/samples/edims_334453.pdf'); \
	sys.stdout.buffer.write(webp)" > docker-thumbnail.webp
	@echo "Testing WebP format and dimensions..."
	@identify docker-thumbnail.webp | grep -q "webp" || (echo "WebP validation failed" && exit 1)
	@echo "File size:"
	@ls -lh docker-thumbnail.webp
	@echo "✓ WebP thumbnail generation works in Docker"

docker/test: ## Run tests in our Docker container
	docker run --rm --platform linux/amd64 crccheck/atx-bandc:test uv run python manage.py test

docker/bash: ## Open a shell in the Docker image
	docker run --rm --platform linux/amd64 -it crccheck/atx-bandc:develop /bin/bash

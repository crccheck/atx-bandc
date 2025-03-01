NAME = bandc
IMAGE = crccheck/atx-bandc:develop

help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

clean:
	rm -rf MANIFEST
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -name ".DS_Store" -delete

# On OSX, tested with ImageMagick 7.0.9-16 and Ghostscript 9.50
# brew install imagemagick gs

# sudo apt-get install -y imagemagick
install: ## Install the project for local dev
	uv sync --all-extras --dev

admin: ## Set up a local insecure admin developer account
	-echo "from django.contrib.auth import get_user_model; \
		User = get_user_model(); \
		User.objects.create_superuser('admin@example.com', 'admin@example.com', 'admin')" | \
		python manage.py shell

lint: ## Check project linting rules
	ruff format --check .
	ruff check .

delint: ## Fix fixable linting errors
	ruff format .
	ruff check . --fix

dev: ## Run the development server
	LOG_LEVEL=$${LOG_LEVEL:-DEBUG} python manage.py runserver 0.0.0.0:8000

test: ## Run test suite
	LOG_LEVEL=$${LOG_LEVEL:-CRITICAL} python manage.py test

tdd: ## Run test watcher
	LOG_LEVEL=$${LOG_LEVEL:-CRITICAL} nodemon -e py -x "python manage.py test --failfast --keepdb ${SCOPE}"

docker/build: ## Build a local dev Docker image
	cp .gitignore .dockerignore
	uv pip compile --upgrade pyproject.toml -o requirements.txt
	docker buildx build --load -t ${IMAGE} --build-arg GIT_SHA=$(shell git rev-parse HEAD) .

docker/publish: ## Build the Docker image
	cp .gitignore .dockerignore
	uv pip compile --upgrade pyproject.toml -o requirements.txt
	docker buildx build --platform linux/amd64 --push -t crccheck/atx-bandc --build-arg GIT_SHA=$(shell git rev-parse HEAD) .

docker/scrape: ## Scrape and process pdfs
	docker run --rm ${IMAGE} python manage.py scrape

docker/run: ## Scrape and process pdfs
	docker run --rm -it -p 8000:8000 -e DATABASE_URL="sqlite:////data/bandc.db" \
	-v $$PWD/bandc:/app/bandc:ro \
	-v $$PWD/bandc.db:/data/bandc.db:rw ${IMAGE}

# This is a good ImageMagic PDF guide:
# https://www.binarytides.com/convert-pdf-image-imagemagick-commandline/
docker/converttest: ## Make sure we can create thumbnails from PDFs in production
	docker run --rm \
	--volume $${PWD}/bandc/apps/agenda/tests/samples:/app/bandc/apps/agenda/tests/samples:ro \
	${IMAGE} \
	convert \
	"./bandc/apps/agenda/tests/samples/edims_354309.pdf[0]" \
	-thumbnail 400x400 \
	-flatten \
	jpg:- > docker-converttest.jpg

docker/bash:
	docker run --rm -it ${IMAGE} /bin/bash

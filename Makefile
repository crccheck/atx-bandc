NAME = bandc
IMAGE = crccheck/atx-bandc:develop
PORT ?= 8000

help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

clean:
	rm -rf MANIFEST
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete

requirements.txt: requirements.in
	pip-compile $< > $@

install: ## Install requirements
	sudo apt-get install -y imagemagick
	pip install -r requirements.txt

workers: ## Start celery workers
	python manage.py celery worker --loglevel=info

serve: ## Serve the wsgi application
	waitress-serve --port=$(PORT) bandc.wsgi:application

db: ## Start the dev database
	docker run --name $(NAME)_db -d \
	  -e POSTGRES_USER=bandc \
	  -e POSTGRES_PASSWORD=bandcdevpassword \
	  postgres:9.5 || docker start $(NAME)_db

resetdb: ## Reset the dev database
	docker rm -f $(NAME)_db
	${MAKE} -s db

test: ## Run test suite
test: clean
	python manage.py test --keepdb

docker/build: ## Build the Docker image
	docker build -t ${IMAGE} .

docker/scrape: ## Scrape and process pdfs
	docker run --rm --env-file=env-prod ${IMAGE} python manage.py scrape

docker/converttest:
	docker run --rm ${IMAGE} \
	convert \
	"./bandc/apps/agenda/tests/samples/document_559F43E9-A324-12E8-80CA01C0F02507A7.pdf" \
	-thumbnail 400x400 \
	-alpha remove \
	jpg:/tmp/test.jpg

docker/bash:
	docker run --rm -it ${IMAGE} /bin/bash

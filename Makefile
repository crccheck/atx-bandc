NAME = bandc
IMAGE = crccheck/$(NAME)
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

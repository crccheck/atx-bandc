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

# On OSX, tested with ImageMagick 7.0.9-16 and Ghostscript 9.50
# brew install imagemagick gs

# sudo apt-get install -y imagemagick
install: ## Install requirements
	pip install -r requirements.txt -r dev-requirements.txt

.PHONY: requirements.txt
requirements.txt: ## Regenerate requirements.txt
	pip-compile requirements.in > $@
	pip-compile dev-requirements.in

admin: ## Set up a local admin/admin developer account
	echo "from django.contrib.auth import get_user_model; \
		User = get_user_model(); \
		User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | \
		python manage.py shell

serve: ## Serve the wsgi application
	waitress-serve --port=$(PORT) bandc.wsgi:application

test: ## Run test suite
	python manage.py test --keepdb

tdd: ## Run test watcher
	nodemon -e py -x "python manage.py test --failfast --keepdb ${SCOPE}"

docker/build: ## Build the Docker image
	docker build -t ${IMAGE} .

docker/scrape: ## Scrape and process pdfs
	docker run --rm --env-file=env-prod ${IMAGE} python manage.py scrape

# This is a good ImageMagic PDF guide:
# https://www.binarytides.com/convert-pdf-image-imagemagick-commandline/
docker/converttest:
	docker run --rm ${IMAGE} \
	convert \
	"./bandc/apps/agenda/tests/samples/document_559F43E9-A324-12E8-80CA01C0F02507A7.pdf" \
	-thumbnail 400x400 \
	-flatten \
	jpg:/tmp/test.jpg

docker/bash:
	docker run --rm -it ${IMAGE} /bin/bash

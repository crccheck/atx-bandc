NAME = bandc
IMAGE = crccheck/$(NAME)

help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

db: ## Start the database
	docker run --name $(NAME)_db -d \
	  -e POSTGRES_USER=bandc \
	  -e POSTGRES_PASSWORD=bandcdevpassword \
	  postgres:9.5 || docker start $(NAME)_db

docker/build: ## Build the Docker image
	docker build -t ${IMAGE} .

docker/scrape: ## Scrape and process pdfs
	docker run --rm --env-file=env-prod ${IMAGE} make scrape pdf

docker/pdf: ## Just process pdfs
	docker run --rm --env-file=env-prod ${IMAGE} make pdf

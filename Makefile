
help:
	@echo "docker/build   Build the Docker image"
	@echo "docker/scrape  Scape and process pdfs"
	@echo "docker/pdf     Just process pdfs"

docker/build:
	docker build -t crccheck/bandc .

docker/scrape:
	docker run --rm --env-file=env-prod crccheck/bandc make scrape pdf

docker/pdf:
	docker run --rm --env-file=env-prod crccheck/bandc make pdf

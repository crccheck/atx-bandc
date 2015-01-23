IMAGE=atx-bandc

help:
	@echo "docker/build   Build the Docker image"
	@echo "docker/scrape  Scape and process pdfs"
	@echo "docker/pdf     Just process pdfs"

docker/build:
	docker build -t crccheck/${IMAGE} .

docker/scrape:
	docker run --rm --env-file=env-prod crccheck/${IMAGE} make scrape pdf

docker/pdf:
	docker run --rm --env-file=env-prod crccheck/${IMAGE} make pdf

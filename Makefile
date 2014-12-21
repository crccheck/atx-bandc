docker/build:
	docker build -t crccheck/bandc .

docker/scrape:
	docker run --rm --env-file=env-prod crccheck/bandc make scrape pdf

docker/pdf:
	docker run --rm --env-file=env-prod crccheck/bandc make pdf

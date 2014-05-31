
test:
	python scraper/tests.py

scraper/samples:
	mkdir -p $@
	curl http://www.austintexas.gov/cityclerk/boards_commissions/meetings/2014_12_1.htm > $@/music.html
	curl http://www.austintexas.gov/cityclerk/boards_commissions/meetings/2014_39_1.htm > $@/parks.html

.PHONY: scraper/samples


test:
	python -m unittest discover

scrape:
	python scrape.py -v

pdf:
	python pdf.py

samples:
	mkdir -p $@
	curl http://www.austintexas.gov/cityclerk/boards_commissions/meetings/2014_12_1.htm > $@/music.html
	curl http://www.austintexas.gov/cityclerk/boards_commissions/meetings/2014_39_1.htm > $@/parks.html
	curl http://www.austintexas.gov/cityclerk/boards_commissions/meetings/2014_39_2.htm > $@/parks2.html

resetdb:
	# assumes postgres
	phd dropdb
	phd createdb


feed:
	python feed.py

.PHONY: samples feed

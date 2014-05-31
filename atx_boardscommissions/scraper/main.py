from lxml.html import parse


def process():
    # TODO use real url
    doc = parse(open('samples/music.html'))
    print doc.xpath('//h5[@class="bcic_mtgdate"]/text()')


if __name__ == '__main__':
    process()

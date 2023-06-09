#!/usr/bin/env python3
import getopt
import sys

from lxml import etree
import random
from urllib.request import urlopen
from urllib.parse import urlencode


def xpath(node, path):
    tree = node.getroottree()
    base_xpath = tree.getpath(node)

    return tree.xpath(base_xpath + path)

class LibgenMirror:
    def __init__(self, url, format, size, unit):
        self.url = url
        self.format = format
        self.size = size
        self.unit = unit

    @staticmethod
    def parse(node, file_type, file_size, file_size_unit):
        url = node.get('href')

        return LibgenMirror(url, file_type, file_size, file_size_unit)

class LibgenBook:
    def __init__(self, title, authors, series, md5, mirrors, language,
                 image_url):
        self.title = title
        self.authors = authors
        self.series = series
        self.md5 = md5
        self.mirrors = mirrors
        self.language = language
        self.image_url = image_url

    @staticmethod
    def parse(node):
        AUTHOR_XPATH = '/td[1]/ul/li/a'
        SERIES_XPATH = '/td[2]'
        TITLE_XPATH = '/td[3]/p/a'
        LANGUAGE_XPATH = '/td[4]'
        FILE_XPATH = '/td[5]'
        MIRRORS_XPATH = '/td[6]//a'

        # Parse the Author(s) column into `authors`
        authors = ' & '.join(filter(None, [
            author.text for author in xpath(node, AUTHOR_XPATH)
        ]))

        if len(authors) == 0:
            authors = 'Unknown'

        # Parse File and Mirrors columns into a list of mirrors
        file_info = xpath(node, FILE_XPATH)[0].text
        file_type, file_size = file_info.split(' / ')
        file_size, file_size_unit = file_size.split('\xa0')

        mirrors = [
            LibgenMirror.parse(n, file_type, file_size, file_size_unit)
            for n in xpath(node, MIRRORS_XPATH)
        ]

        # Parse other columns
        series = xpath(node, SERIES_XPATH)[0].text
        title = xpath(node, TITLE_XPATH)[0].text
        md5 = xpath(node, TITLE_XPATH)[0].get('href').split('/')[-1]
        language = xpath(node, LANGUAGE_XPATH)[0].text

        if not authors or not title:
            return None

        return LibgenBook(title, authors, series, md5, mirrors, language, None)


class LibgenSearchResults:
    def __init__(self, results, total):
        self.results = results
        self.total = total

    @staticmethod
    def parse(node):
        SEARCH_ROW_SELECTOR = "/body/table/tbody/tr"

        result_rows = xpath(node, SEARCH_ROW_SELECTOR)

        results = []

        for row in result_rows:
            book = LibgenBook.parse(row)
            if book is None:
                continue

            results.append(book)

        total = len(results)

        return LibgenSearchResults(results, total)


class LibgenFictionClient:
    def __init__(self, mirror=None):

        MIRRORS = [
            "libgen.rs",
            "libgen.is",
            # "libgen.lc",  # Still has the old-style search
            "gen.lib.rus.ec",
            "93.174.95.27",
        ]

        if mirror is None:
            self.base_url = "http://{}/fiction/".format(MIRRORS[0])
        else:
            self.base_url = "http://{}/fiction/".format(mirror)

    def search(self, query, criteria='', language='English', file_format=''):
        url = self.base_url
        query_params = {
            'q': query,
            'criteria': criteria,
            'language': language,
            'format': file_format,
        }

        query_string = urlencode(query_params)
        request = urlopen(url + '?' + query_string)
        html = request.read()

        parser = etree.HTMLParser()
        tree = etree.fromstring(html, parser)

        return LibgenSearchResults.parse(tree)

    def get_detail_url(self, md5):
        detail_url = '{}{}'.format(self.base_url, md5)

        return detail_url

    def get_download_url(self, md5):
        download_urls = [
            'http://library.lol/fiction/{}'.format(md5),
        ]

        for url in download_urls:
            try:
                request = urlopen(url)
                html = request.read()

                parser = etree.HTMLParser()
                tree = etree.fromstring(html, parser)

                SELECTOR = "//h2/a[contains(., 'GET')]"
                SELECTOR = "//a[contains(., 'GET')]"
                link = tree.xpath(SELECTOR)
                return link[0].get('href')
            except:
                continue

def main(argv):
    client = LibgenFictionClient()

    opts, args = getopt.getopt(argv, "hq:t:a:s:l:f:", ["query=", "title=", "author=", "series=", "language=", "format="])
    query = ""
    criteria = ""
    file_format = "epub"
    language = "English"

    for opt, arg in opts:
        if opt == '-h':
            print('USAGE: libgen_client.py -q <query> -t <title> -a <author> -s <series> -l <language> -f <format>')
            print('Only one of query, title, author, or series may be used at a time')
            sys.exit()
        elif opt in ("-q", "--query"):
            query = arg
        elif opt in ("-t", "--title"):
            criteria = "title"
            query = arg
        elif opt in ("-a", "--author"):
            query = arg
            criteria = "authors"
        elif opt in ("-s", "--series"):
            criteria = "series"
        elif opt in ("-l", "--language"):
            language = arg
        elif opt in ("-f", "--format"):
            file_format = arg

    search_results = client.search(query, criteria, language, file_format)


    for result in search_results.results[:5]:
        print(result.title+" by "+result.authors)
        print("Detail", client.get_detail_url(result.md5))
        print("Download", client.get_download_url(result.md5))


if __name__ == "__main__":
    main(sys.argv[1:])

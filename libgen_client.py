DEFAULT_FIELDS = "Title,Author,ID,MD5"

LIBGEN_URL = "http://libgen.io/foreignfiction/"

BOOK_ENDPOINT =  "json.php?ids={0}&fields={1}"
DOWNLOAD_URL = "get.php?md5={0}"
SEARCH_URL = "index.php"

ID_REGEX = "\?id=[0-9]+"

import requests
import json
from collections import namedtuple
from lxml import etree

import re


def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

def xpath(node, path):
    tree = node.getroottree()
    base_xpath = tree.getpath(node)

    return tree.xpath(base_xpath + path)

class LibgenDownload:
    def __init__(self, url, format, size, unit):
        self.url = url
        self.format = format
        self.size = size
        self.unit = unit

    @staticmethod
    def parse(node):
        DOWNLOAD_REGEX = "([A-z0-9]+)\(([0-9]+)([A-z]+)\)"

        text = node.text
        match = re.match(DOWNLOAD_REGEX, text)

        if not match:
            return None

        url = node.get('href')

        format = match.group(1)
        size = match.group(2)
        unit = match.group(3)

        return LibgenDownload(url, format, size, unit)

class LibgenBook:
    def __init__(self, title, author, series, downloads, language):
        self.title = title
        self.author = author
        self.series = series
        self.downloads = downloads
        self.language = language

    @staticmethod
    def parse(node):
        AUTHOR_XPATH = '/td[1]/a'
        SERIES_XPATH = '/td[2]'
        TITLE_XPATH = '/td[3]'
        LANGUAGE_XPATH = '/td[4]'
        DOWNLOADS_XPATH = '/td[5]/div/a[1]'

        author = xpath(node, AUTHOR_XPATH)[0].text
        series = xpath(node, SERIES_XPATH)[0].text
        title = xpath(node, TITLE_XPATH)[0].text
        language = xpath(node, LANGUAGE_XPATH)[0].text

        downloads_nodes = xpath(node, DOWNLOADS_XPATH)
        downloads = [LibgenDownload.parse(n) for n in downloads_nodes]

        return LibgenBook(title, author, series, downloads, language)

class LibgenSearchResults:
    def __init__(self, results, total):
        self.results = results
        self.total = total

    @staticmethod
    def parse(node):
        SEARCH_ROW_SELECTOR = "//table[2]//tr"

        result_rows = xpath(node, SEARCH_ROW_SELECTOR)

        results = [LibgenBook.parse(row) for row in result_rows]
        total = 0

        return LibgenSearchResults(results, total)

class LibgenFictionClient:
    def __init__(self, base_url=LIBGEN_URL):
        self.base_url = base_url

    def search(self, query):
        url = self.base_url + SEARCH_URL
        query_params = {
            's': query,
            'f_group': 1
        }

        response = requests.get(url, params=query_params)

        parser = etree.HTMLParser()
        tree = etree.fromstring(response.text, parser)

        return LibgenSearchResults.parse(tree)


if __name__ == "__main__":
    client = LibgenClient()
    result = client.search("Stormlight Archive")
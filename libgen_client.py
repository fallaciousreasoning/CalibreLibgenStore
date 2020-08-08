from lxml import etree
import re
import urllib

MIRRORS = [
    "libgen.is",
    "gen.lib.rus.ec",
    "93.174.95.27",
]

BASE_URL = "http://{0}/".format(MIRRORS[0])
LIBGEN_URL = "{0}fiction/".format(BASE_URL)

BOOK_ENDPOINT =  "json.php?ids={0}&fields={1}"
DOWNLOAD_URL = "get.php?md5={0}"
SEARCH_URL = ""

ID_REGEX = "\?id=[0-9]+"

DEFAULT_FIELDS = "Title,Author,ID,MD5"

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
    def parse(node, file_type, file_size, file_size_unit):
        url = node.get('href')

        return LibgenDownload(url, file_type, file_size, file_size_unit)

class LibgenBook:
    def __init__(self, title, author, series, downloads, language, image_url):
        self.title = title
        self.author = author
        self.series = series
        self.downloads = downloads
        self.language = language
        self.image_url = image_url

    @staticmethod
    def parse(node):
        AUTHOR_XPATH = '/td[1]//a'
        SERIES_XPATH = '/td[2]'
        TITLE_XPATH = '/td[3]/a'
        LANGUAGE_XPATH = '/td[4]'
        FILE_XPATH = '/td[5]'
        DOWNLOADS_XPATH = '/td[6]//a'

        author_result = xpath(node, AUTHOR_XPATH)
        author = ' & '.join([result.text for result in author_result])\
            if len(author_result) > 0\
            else 'Unknown'
        series = xpath(node, SERIES_XPATH)[0].text
        title = xpath(node, TITLE_XPATH)[0].text
        language = xpath(node, LANGUAGE_XPATH)[0].text
        file_info = xpath(node, FILE_XPATH)[0].text.encode('utf-8')
        file_type, file_size = file_info.split(' / ')
        file_size, file_size_unit = file_size.split('\xc2\xa0')

        downloads_nodes = xpath(node, DOWNLOADS_XPATH)
        downloads = [
            LibgenDownload.parse(n, file_type, file_size, file_size_unit)
            for n in downloads_nodes]

        if not author and not title:
            return None

        return LibgenBook(title, author, series, downloads, language, None)

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
    def __init__(self, base_url=LIBGEN_URL):
        self.base_url = base_url

    def search(self, query):
        url = self.base_url + SEARCH_URL
        query_params = {
            'q': query,
            'criteria': '',
            'language': '',
            'format': '',
        }

        query_string = urllib.urlencode(query_params)
        request = urllib.urlopen(url + '?' + query_string)
        html = request.read()

        parser = etree.HTMLParser()
        tree = etree.fromstring(html, parser)

        return LibgenSearchResults.parse(tree)


if __name__ == "__main__":
    client = LibgenFictionClient()
    search_results = client.search("shadows on the grass")

    for result in search_results.results:
        print(result.title)

from lxml import etree
import re
import urllib

MIRRORS = [
    "libgen.is",
    "gen.lib.rus.ec",
    "93.174.95.27",
]

BASE_URL = "http://{0}/".format(MIRRORS[0])
LIBGEN_URL = "{0}foreignfiction/".format(BASE_URL)

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
    def parse(node):
        DOWNLOAD_REGEX = "([A-z0-9]+)\(([0-9]+)([A-z]+)\)"

        text = node.text
        match = re.match(DOWNLOAD_REGEX, text)

        if not match:
            return None

        url = BASE_URL + node.get('href').replace('ads.php', 'get.php')

        format = match.group(1)
        size = match.group(2)
        unit = match.group(3)

        return LibgenDownload(url, format, size, unit)

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
        AUTHOR_XPATH = '/td[1]/a'
        SERIES_XPATH = '/td[2]'
        TITLE_XPATH = '/td[3]'
        LANGUAGE_XPATH = '/td[4]'
        DOWNLOADS_XPATH = '/td[5]/div/a[1]'
        IMAGE_REGEX = re.compile("\&lt\;img src=\"?/(fictioncovers/.*?)\"? .*?\&gt\;")

        author_result = xpath(node, AUTHOR_XPATH)
        author = author_result[0].text if len(author_result) > 0 else 'Unknown'
        series = xpath(node, SERIES_XPATH)[0].text
        title = xpath(node, TITLE_XPATH)[0].text
        language = xpath(node, LANGUAGE_XPATH)[0].text

        downloads_nodes = xpath(node, DOWNLOADS_XPATH)
        downloads = [LibgenDownload.parse(n) for n in downloads_nodes]

        if not author or not title:
            return None

        raw_html = etree.tostring(node)
        image_match = IMAGE_REGEX.search(raw_html)
        image_url = BASE_URL + image_match.groups(1)[0] if image_match is not None else None

        return LibgenBook(title, author, series, downloads, language, image_url)

class LibgenSearchResults:
    def __init__(self, results, total):
        self.results = results
        self.total = total

    @staticmethod
    def parse(node):
        SEARCH_ROW_SELECTOR = "//body/table[last()]//tr"

        result_rows = xpath(node, SEARCH_ROW_SELECTOR)

        results = []
        for row in result_rows:
            book = LibgenBook.parse(row)
            if book is None: continue

            results.append(book)

        total = 0

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
            'format': 'epub',
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

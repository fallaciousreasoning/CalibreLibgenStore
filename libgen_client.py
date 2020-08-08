from lxml import etree
import random
import urllib



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
        AUTHOR_XPATH = '/td[1]//a'
        SERIES_XPATH = '/td[2]'
        TITLE_XPATH = '/td[3]/a'
        LANGUAGE_XPATH = '/td[4]'
        FILE_XPATH = '/td[5]'
        MIRRORS_XPATH = '/td[6]//a'

        # Parse the Author(s) column into `authors`
        authors = ' & '.join([
            author.text for author in xpath(node, AUTHOR_XPATH)
        ])

        if len(authors) == 0:
            authors = 'Unknown'

        # Parse File and Mirrors columns into a list of mirrors
        file_info = xpath(node, FILE_XPATH)[0].text.encode('utf-8')
        file_type, file_size = file_info.split(' / ')
        file_size, file_size_unit = file_size.split('\xc2\xa0')

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
            "libgen.is",
            # "libgen.lc",  # Still has the old-style search
            "gen.lib.rus.ec",
            "93.174.95.27",
        ]

        if mirror is None:
            self.base_url = "http://{}/fiction/".format(random.choice(MIRRORS))
        else:
            self.base_url = "http://{}/fiction/".format(mirror)

    def search(self, query):
        url = self.base_url
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

    def get_detail_url(self, md5):
        detail_url = '{}{}'.format(self.base_url, md5)

        return detail_url


if __name__ == "__main__":
    client = LibgenFictionClient()
    search_results = client.search("shadows on the grass")

    for result in search_results.results:
        print(result.title)

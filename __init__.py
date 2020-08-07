# -*- coding: utf-8 -*-

from __future__ import (unicode_literals, division, absolute_import, print_function)
store_version = 5  # Needed for dynamic plugin loading

__license__ = 'MIT'
__copyright__ = 'Fallacious Reasoning'
__docformat__ = 'restructuredtext en'

#####################################################################
# Plug-in base class
#####################################################################

# from calibre.customize import InterfaceActionBase

PLUGIN_NAME = 'Libgen Fiction'
PLUGIN_DESCRIPTION = 'Adds a Libgen Fiction search provider to Calibre'
PLUGIN_VERSION_TUPLE = (0, 1, 0)
PLUGIN_VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])
PLUGIN_AUTHORS = "Fallacious Reasoning (https://github.com/fallaciousreasoning/CalibreLibgenStore)"

#####################################################################

# import base64
# import mimetypes
# import re
# import urllib
# import urllib2
# from contextlib import closing

# from lxml import etree

from .libgen_client import LibgenFictionClient

# from calibre import browser, url_slash_cleaner
# from calibre.constants import __appname__, __version__
# from calibre.gui2.store.basic_config import BasicStoreConfig
from calibre.gui2.store.search_result import SearchResult
from calibre.gui2.store import StorePlugin

from calibre.customize import StoreBase


libgen = LibgenFictionClient()

def search(query, max_results=10, timeout=60):
    libgen_results = libgen.search(query)
    for result in libgen_results.results[:min(max_results, len(libgen_results.results))]:
        s = SearchResult()

        s.title = result.title
        s.author = result.author
        s.series = result.series
        s.language = result.language

        for download in result.downloads:
            s.downloads[download.format] = download.url

        s.formats = ', '.join(s.downloads.keys())
        s.drm = SearchResult.DRM_UNLOCKED
        s.cover_url = result.image_url

        # don't show results with no downloads
        if not s.formats:
            continue

        yield s


class LibgenStore(StorePlugin):
    def search(self, query, max_results=10, timeout=60):
        '''
            Searches LibGen for Books
        '''
        for result in search(query, max_results, timeout):
            yield result

if __name__ == '__main__':
    import sys

    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "Stormlight Archive"
    for result in search(' '.join(sys.argv[1:])):
        print('=========================================================================================================\nTitle: {0}\nAuthor: {1}\nSeries: {2}\nLanguage: {3}\nDownloads: {4}'.format(result.title, result.author, result.series, result.language, len(result.downloads)))

class LibgenStoreWrapper(StoreBase):
    name                    = PLUGIN_NAME
    description             = PLUGIN_DESCRIPTION
    supported_platforms     = ['windows', 'osx', 'linux']
    author                  = PLUGIN_AUTHORS
    version                 = PLUGIN_VERSION_TUPLE
    minimum_calibre_version = (1, 0, 0)
    affiliate               = False

    def load_actual_plugin(self, gui):
        '''
        This method must return the actual interface action plugin object.
        '''
        #mod, cls = self.actual_plugin.split(':')
        store = LibgenStore(gui, self.name)
        self.actual_plugin_object  = store#getattr(importlib.import_module(mod), cls)(gui, self.name)
        return self.actual_plugin_object

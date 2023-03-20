#!/usr/bin/env python3

from functools import partial

from calibre.constants import numeric_version
from calibre.customize import StoreBase
from calibre.devices.usbms.driver import debug_print as root_debug_print
from calibre.gui2 import open_url
from calibre.gui2.store import StorePlugin
from calibre.gui2.store.search_result import SearchResult
from calibre.gui2.store.web_store_dialog import WebStoreDialog
from PyQt5.Qt import QUrl

from calibre_plugins.libgen_fiction.libgen_client import LibgenFictionClient

if numeric_version >= (5, 5, 0):
    module_debug_print = partial(root_debug_print, ' the_eye:__init__:', sep='')
else:
    module_debug_print = partial(root_debug_print, 'the_eye:__init__:')

__license__        = 'MIT'
__copyright__      = 'fallaciousreasoning'
__docformat__      = 'restructuredtext en'

PLUGIN_NAME        = 'Libgen Fiction'
PLUGIN_DESCRIPTION = 'Adds a Libgen Fiction search provider to calibre'
PLUGIN_AUTHORS     = 'fallaciousreasoning (https://github.com/fallaciousreasoning/CalibreLibgenStore)'
PLUGIN_VERSION     = (0, 4, 0)

class LibgenStore(StorePlugin):
    def genesis(self):
        """Initialize the Libgen Client
        """
        debug_print = partial(module_debug_print, 'LibgenStore:genesis:')
        debug_print('start')

        self.libgen = LibgenFictionClient()

    def search(self, query, max_results=10, timeout=60):
        """Searches LibGen for Books. Since the mirror links are not direct
        downloads, it should not provide these as `s.downloads`.
        """
        if not hasattr(self, 'libgen'):
            self.genesis() 

        debug_print = partial(module_debug_print, 'LibgenStore:search:')
        debug_print('search:query = ', query)

        libgen_results = self.libgen.search(query)

        for result in libgen_results.results[:min(max_results, len(libgen_results.results))]:
            debug_print('result.title = ', result.title)

            for mirror in result.mirrors[0:1]:  # Calibre only shows 1 anyway
                debug_print('result.mirror.url = ', mirror.url)

                s = SearchResult()

                s.store_name = PLUGIN_NAME
                s.cover_url = result.image_url
                s.title = '{} ({}, {}{})'.format(
                    result.title, result.language, mirror.size, mirror.unit)
                s.author = result.authors
                s.price = '0.00'
                s.detail_item = result.md5
                s.drm = SearchResult.DRM_UNLOCKED
                s.formats = mirror.format
                s.plugin_author = PLUGIN_AUTHORS

                debug_print('s = ', s)

                yield s

    def open(self, parent=None, detail_item=None, external=False):
        """Open the specified item in the external, or Calibre's browser
        """
        debug_print = partial(module_debug_print, 'LibgenStore:open:')
        debug_print('locals() = ', locals())

        if not hasattr(self, 'libgen'):
            self.genesis() 

        detail_url = (
            self.libgen.get_detail_url(detail_item)
            if detail_item
            else self.libgen.base_url
        )

        debug_print('detail_url = ', detail_url)

        if external or self.config.get('open_external', False):
            open_url(QUrl(detail_url))
        else:
            d = WebStoreDialog(
                self.gui, self.libgen.base_url, parent, detail_url)
            d.setWindowTitle(self.name)
            d.set_tags(self.config.get('tags', ''))
            d.exec_()

    def get_details(self, search_result, details):
        url = self.libgen.get_detail_url(search_result.detail_item)
        download = self.libgen.get_download_url(search_result.detail_item)
        search_result.downloads[search_result.formats] = download

class LibgenStoreWrapper(StoreBase):
    name                    = PLUGIN_NAME
    description             = PLUGIN_DESCRIPTION
    author                  = PLUGIN_AUTHORS
    version                 = PLUGIN_VERSION
    minimum_calibre_version = (5, 0, 1)  # Because Python 3
    affiliate               = False
    drm_free_only           = True

    def load_actual_plugin(self, gui):
        """This method must return the actual interface action plugin object.
        """
        self.actual_plugin_object  = LibgenStore(gui, self.name)
        return self.actual_plugin_object

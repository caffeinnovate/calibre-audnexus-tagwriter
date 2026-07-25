import sys

from calibre.customize import InterfaceActionBase


class AudnexusBulkUpdaterPlugin(InterfaceActionBase):
    # Keep this identifier stable: Calibre keys custom-plugin installation and
    # removal by ``name``, independently of the toolbar action label.
    name = 'Audnexus Tag Writer'
    description = 'Update every Calibre-managed MP3/M4B audiobook for Plex Audnexus.'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Caffeinnovate'
    version = (1, 0, 3)
    minimum_calibre_version = (7, 0, 0)
    actual_plugin = 'calibre_plugins.audnexus_tag_writer.ui:AudnexusBulkUpdateAction'

    def initialize(self):
        if self.plugin_path and self.plugin_path not in sys.path:
            sys.path.insert(0, self.plugin_path)

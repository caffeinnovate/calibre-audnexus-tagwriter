import sys

from calibre.customize import MetadataWriterPlugin


class AudnexusMetadataWriter(MetadataWriterPlugin):
    name = 'Audnexus Audiobook Metadata Writer'
    description = 'Write Calibre metadata to MP3 and M4B files for Plex Audnexus.'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Caffeinnovate'
    version = (1, 0, 2)
    minimum_calibre_version = (7, 0, 0)
    file_types = {'mp3', 'm4b'}

    def initialize(self):
        if self.plugin_path and self.plugin_path not in sys.path:
            sys.path.insert(0, self.plugin_path)

    def customization_help(self, gui=False):
        return 'Set to clear_missing to remove managed audio tags when the matching Calibre value is empty. The default preserves them.'

    def set_metadata(self, stream, mi, file_type):
        # Metadata writer plugins run inside Calibre's format-embedding job.
        # Use Calibre's debug logger so a successful invocation is visible when
        # Calibre is started with ``calibre-debug -g``.
        from calibre import prints
        from calibre_plugins.audnexus_metadata_writer.metadata import book_tags
        from calibre_plugins.audnexus_metadata_writer.audio import write_audio

        clear_missing = (self.site_customization or '').strip().lower() == 'clear_missing'
        values = book_tags(mi, getattr(mi, 'cover_data', None))
        prints(
            'Audnexus metadata writer: writing',
            file_type.upper(),
            'metadata for:',
            getattr(mi, 'title', '') or '<untitled>',
            '(clear missing tags:', clear_missing, ')',
        )
        write_audio(stream, values, clear_missing=clear_missing, file_type=file_type)
        prints(
            'Audnexus metadata writer: completed',
            file_type.upper(),
            'metadata for:',
            getattr(mi, 'title', '') or '<untitled>',
        )

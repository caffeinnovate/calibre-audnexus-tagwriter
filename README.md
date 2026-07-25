# Audnexus Tag Writer for Calibre

This repository contains two Calibre 7+ plugins for writing audiobook metadata to Calibre-managed MP3 and M4B formats. They are designed to help Plex's legacy [Audnexus Agent](https://github.com/djdembeck/Audnexus.bundle) match audiobooks.

## Build and install

Run `python build_plugin.py`. This downloads Mutagen into a temporary build directory and creates two self-contained release ZIPs:

- `dist/AudnexusMetadataWriter.zip` integrates with Calibre's normal **Write metadata to files** process for MP3/M4B.
- `dist/AudnexusBulkAudiobookUpdate.zip` adds **Update all audiobooks**, which previews and updates every managed MP3/M4B in the current library.

Install both via **Preferences → Plugins → Load plugin from file**. Restart Calibre if prompted.

## Use

Use Calibre's normal **Write metadata to files** process for routine MP3/M4B updates. The metadata writer preserves existing audio values when the matching Calibre field is empty. In **Preferences → Plugins → Customize plugin**, enter `clear_missing` to remove those managed tags instead.

Choose **Update all audiobooks** from the plugin toolbar/menu for a library-wide update. It only touches attached Calibre-managed `MP3` and `M4B` formats, previews every pending update, and lets you choose whether absent Calibre values preserve or clear the corresponding audio tag.

Make a backup before changing media files. The plugin never renames, moves, exports, re-encodes, or changes chapters/audio streams.

## Tag mapping

| Audio tag | Calibre source |
| --- | --- |
| Title, Album | Title |
| Artist, Album artist | Authors, joined with ` & ` |
| Album sort | Series and zero-padded series index |
| Grouping | Series |
| Publisher, date, description, genre, rating | Matching standard Calibre metadata |
| ASIN | Identifier key exactly named `asin` |
| Front cover | Current Calibre cover |

Narrator/composer/style tags are deliberately left alone because Calibre has no standard narrator field. Unrelated tags are retained.

## Plex and Audnexus

Create a Plex **Music** library using **Plex Music Scanner** and the **Audnexus Agent**, with embedded genres and local album art enabled. Audnexus documents `album` and `albumartist` as imperative for matching and recommends a separate `Author/Book/Book.m4b` library layout. This plugin writes tags only; arrange any Plex-facing copy independently.

## Tests

Run `python -m pytest tests`. The packaged plugins can be checked with:

```powershell
& 'C:\Program Files\Calibre2\calibre-customize.exe' -a .\dist\AudnexusMetadataWriter.zip
& 'C:\Program Files\Calibre2\calibre-customize.exe' -a .\dist\AudnexusBulkAudiobookUpdate.zip
```

"""Book discovery and write orchestration, separate from Calibre UI code."""

from __future__ import annotations

import os

from calibre_plugins.audnexus_tag_writer.audio import write_audio
from calibre_plugins.audnexus_tag_writer.metadata import book_tags


SUPPORTED_FORMATS = frozenset(('MP3', 'M4B'))


def audio_paths(db, book_id):
    formats = set((db.formats(book_id, verify_formats=False) or '').upper().split(','))
    paths = []
    for fmt in sorted(formats & SUPPORTED_FORMATS):
        path = db.format_abspath(book_id, fmt)
        if path and os.path.isfile(path):
            paths.append(path)
    return paths


def build_jobs(db, book_ids):
    jobs, skipped = [], []
    for book_id in book_ids:
        paths = audio_paths(db, book_id)
        if not paths:
            skipped.append((book_id, 'No Calibre-managed MP3 or M4B format'))
            continue
        mi = db.get_metadata(book_id, get_cover=False)
        cover = db.cover(book_id, as_file=False)
        values = book_tags(mi, cover)
        for path in paths:
            jobs.append((book_id, path, values))
    return jobs, skipped


def write_jobs(jobs, clear_missing):
    updated, failures = [], []
    for book_id, path, values in jobs:
        try:
            write_audio(path, values, clear_missing)
        except Exception as err:
            failures.append((book_id, path, str(err)))
        else:
            updated.append((book_id, path))
    return updated, failures

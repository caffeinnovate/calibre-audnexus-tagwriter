"""Book discovery and write orchestration, separate from Calibre UI code."""

from __future__ import annotations

import os

from calibre_plugins.audnexus_tag_writer.audio import read_existing_tags, write_audio
from calibre_plugins.audnexus_tag_writer.metadata import book_tags


SUPPORTED_FORMATS = frozenset(('MP3', 'M4B'))


def audio_paths(db, book_id):
    formats = {fmt.upper() for fmt in (db.formats(book_id, verify_formats=False) or ())}
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
            jobs.append((book_id, path, values, read_existing_tags(path)))
    return jobs, skipped


def build_jobs_in_background(db, book_ids, abort, log, notifications):
    """Discover files and read preview values without blocking Calibre's UI."""
    jobs, skipped = [], []
    total = len(book_ids)
    for index, book_id in enumerate(book_ids, start=1):
        if abort.is_set():
            log('Audiobook tag update preparation cancelled by user')
            return jobs, skipped, True
        notifications.put(((index - 1) / total, 'Preparing audiobook {}/{}'.format(index, total)))
        paths = audio_paths(db, book_id)
        if not paths:
            skipped.append((book_id, 'No Calibre-managed MP3 or M4B format'))
            continue
        mi = db.get_metadata(book_id, get_cover=False)
        cover = db.cover(book_id, as_file=False)
        values = book_tags(mi, cover)
        for path in paths:
            jobs.append((book_id, path, values, read_existing_tags(path)))
        notifications.put((index / total, 'Prepared audiobook {} of {}'.format(index, total)))
    return jobs, skipped, False


def write_jobs(jobs, clear_missing):
    updated, failures = [], []
    for book_id, path, values, _old_values in jobs:
        try:
            write_audio(path, values, clear_missing)
        except Exception as err:
            failures.append((book_id, path, str(err)))
        else:
            updated.append((book_id, path))
    return updated, failures


def write_jobs_in_background(jobs, clear_missing, abort, log, notifications):
    """Write audiobook tags in a Calibre threaded job and report live progress."""
    updated, failures = [], []
    total = len(jobs)
    for index, (book_id, path, values, _old_values) in enumerate(jobs, start=1):
        if abort.is_set():
            log('Audiobook tag update cancelled by user')
            return updated, failures, True
        notifications.put(((index - 1) / total, 'Updating {} ({}/{})'.format(os.path.basename(path), index, total)))
        try:
            write_audio(path, values, clear_missing)
        except Exception as err:
            log.exception('Unable to update {}: {}'.format(path, err))
            failures.append((book_id, path, str(err)))
        else:
            updated.append((book_id, path))
        notifications.put((index / total, 'Updated {} of {} files'.format(index, total)))
    return updated, failures, False

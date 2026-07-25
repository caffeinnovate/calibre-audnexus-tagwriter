"""Format-independent metadata mapping used by the UI and audio writers."""

from __future__ import annotations

from datetime import date, datetime


FIELD_LABELS = {
    'title': 'Title', 'album': 'Album', 'albumartist': 'Album artist',
    'artist': 'Artist', 'albumsort': 'Album sort', 'grouping': 'Grouping',
    'publisher': 'Publisher', 'date': 'Date', 'comment': 'Description',
    'genre': 'Genre', 'rating': 'Rating', 'asin': 'ASIN', 'cover': 'Cover art',
}


def join_authors(authors):
    return ' & '.join(a for a in (authors or ()) if a)


def series_sort(series, series_index):
    if not series:
        return None
    try:
        index = float(series_index)
    except (TypeError, ValueError):
        index = 0.0
    return '{} {:07.3f}'.format(series, index)


def date_text(value):
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return str(value) if value else None


def first_asin(identifiers):
    for key, value in (identifiers or {}).items():
        if str(key).lower() == 'asin' and value:
            return str(value).strip() or None
    return None


def book_tags(mi, cover_data=None):
    """Return only meaningful Calibre values; absent values are intentionally omitted."""
    authors = join_authors(getattr(mi, 'authors', ()))
    tags = getattr(mi, 'tags', None) or ()
    rating = getattr(mi, 'rating', None)
    values = {
        'title': getattr(mi, 'title', None),
        'album': getattr(mi, 'title', None),
        'albumartist': authors or None,
        'artist': authors or None,
        'albumsort': series_sort(getattr(mi, 'series', None), getattr(mi, 'series_index', None)),
        'grouping': getattr(mi, 'series', None),
        'publisher': getattr(mi, 'publisher', None),
        'date': date_text(getattr(mi, 'pubdate', None)),
        'comment': getattr(mi, 'comments', None),
        'genre': '; '.join(tags) if tags else None,
        'rating': rating if rating is not None else None,
        'asin': first_asin(getattr(mi, 'identifiers', None)),
        'cover': cover_data,
    }
    return {key: value for key, value in values.items() if value not in (None, '')}

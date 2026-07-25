from datetime import datetime
import importlib.util
from pathlib import Path
from types import SimpleNamespace


SPEC = importlib.util.spec_from_file_location('audnexus_tag_writer_metadata', Path(__file__).parents[1] / 'calibre_plugin' / 'metadata.py')
METADATA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(METADATA)
book_tags = METADATA.book_tags
first_asin = METADATA.first_asin
join_authors = METADATA.join_authors
series_sort = METADATA.series_sort


def test_mapping_from_standard_calibre_fields():
    mi = SimpleNamespace(
        title='Book', authors=['Ada Author', 'Bea Writer'], series='Saga', series_index=2,
        publisher='Publisher', pubdate=datetime(2024, 3, 1), comments='<p>Summary</p>',
        tags=['Fantasy', 'Audio'], rating=8, identifiers={'isbn': '123', 'asin': 'B012345678'},
    )
    values = book_tags(mi, b'cover')
    assert values['album'] == 'Book'
    assert values['albumartist'] == 'Ada Author & Bea Writer'
    assert values['albumsort'] == 'Saga 002.000'
    assert values['grouping'] == 'Saga'
    assert values['asin'] == 'B012345678'
    assert values['cover'] == b'cover'


def test_optional_values_are_omitted_and_asin_is_strict():
    mi = SimpleNamespace(title='Book', authors=[], series=None, series_index=None, publisher=None,
                         pubdate=None, comments=None, tags=[], rating=None, identifiers={'audible': 'B1'})
    values = book_tags(mi)
    assert 'publisher' not in values
    assert 'asin' not in values
    assert first_asin({'ASIN': ' X '}) == 'X'


def test_author_joining_and_series_sort_are_deterministic():
    assert join_authors(['A', '', 'B']) == 'A & B'
    assert series_sort('Series', '1.5') == 'Series 001.500'
    assert series_sort(None, 1) is None

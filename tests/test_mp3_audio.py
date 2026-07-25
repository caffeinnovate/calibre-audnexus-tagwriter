import importlib.util
from pathlib import Path

from mutagen.id3 import ID3


SPEC = importlib.util.spec_from_file_location('audnexus_tag_writer_audio', Path(__file__).parents[1] / 'calibre_plugin' / 'audio.py')
AUDIO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIO)


def test_mp3_writer_round_trips_and_honors_clear_mode(tmp_path):
    path = tmp_path / 'book.mp3'
    path.touch()
    values = {
        'title': 'Book', 'album': 'Book', 'albumartist': 'Author', 'artist': 'Author',
        'publisher': 'Publisher', 'asin': 'B012345678', 'rating': 8,
        'cover': b'\xff\xd8\xff\xe0minimal-jpeg',
    }
    AUDIO.write_mp3(str(path), values)
    tags = ID3(path)
    assert tags.get('TIT2').text == ['Book']
    assert tags.get('TPE2').text == ['Author']
    assert tags.get('TXXX:ASIN').text == ['B012345678']
    assert tags.get('APIC:Cover').data == values['cover']
    assert tags.get('TPUB').text == ['Publisher']

    AUDIO.write_mp3(str(path), {'title': 'New title'}, clear_missing=False)
    assert ID3(path).get('TPUB').text == ['Publisher']
    AUDIO.write_mp3(str(path), {'title': 'New title'}, clear_missing=True)
    assert ID3(path).get('TPUB') is None

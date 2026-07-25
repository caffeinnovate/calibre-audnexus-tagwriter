"""Mutagen writers for MP3 (ID3) and M4B (MP4) audiobook files."""

from __future__ import annotations

from mutagen.id3 import APIC, COMM, ID3, ID3NoHeaderError, POPM, TCON, TDRC, TALB, TIT1, TIT2, TPE1, TPE2, TPUB, TSOA, TXXX
from mutagen.mp4 import MP4, MP4Cover


ID3_FRAMES = {
    'title': TIT2, 'album': TALB, 'albumartist': TPE2, 'artist': TPE1,
    'albumsort': TSOA, 'grouping': TIT1, 'publisher': TPUB, 'date': TDRC,
    'genre': TCON,
}
MP4_KEYS = {
    'title': '\xa9nam', 'album': '\xa9alb', 'albumartist': 'aART', 'artist': '\xa9ART',
    'albumsort': 'soal', 'grouping': '\xa9grp', 'publisher': '----:com.apple.iTunes:PUBLISHER',
    'date': '\xa9day', 'comment': '\xa9cmt', 'genre': '\xa9gen',
    'asin': '----:com.apple.iTunes:ASIN', 'rating': '----:com.apple.iTunes:RATING',
}


def _text_value(value):
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    return str(value) if value not in (None, '') else None


def read_existing_tags(path):
    """Return existing values for the tags this plugin manages, for preview only."""
    extension = str(path).rsplit('.', 1)[-1].lower()
    try:
        if extension == 'mp3':
            tags = ID3(path)
            values = {field: _text_value(getattr(tags.get(frame.__name__), 'text', None)) for field, frame in ID3_FRAMES.items()}
            values['comment'] = _text_value(getattr(tags.getall('COMM')[0], 'text', None)) if tags.getall('COMM') else None
            values['asin'] = _text_value(getattr(tags.get('TXXX:ASIN'), 'text', None))
            popm = tags.get('POPM:calibre@local')
            values['rating'] = str(round(popm.rating / 25.5, 1)) if popm else None
            values['cover'] = bool(tags.getall('APIC'))
            return values
        if extension == 'm4b':
            tags = MP4(path).tags or {}
            values = {field: _text_value(tags.get(atom)) for field, atom in MP4_KEYS.items()}
            values['cover'] = bool(tags.get('covr'))
            return values
    except Exception:
        pass
    return {}


def _set_or_clear(mapping, key, value, clear_missing, set_value, remove_value):
    if value is not None:
        set_value(mapping[key], value)
    elif clear_missing:
        remove_value(mapping[key])


def _image_mime(data):
    return 'image/png' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg'


def _is_png(data):
    return data.startswith(b'\x89PNG\r\n\x1a\n')


def write_mp3(path, values, clear_missing=False):
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()
    for key, frame_type in ID3_FRAMES.items():
        value = values.get(key)
        frame_id = frame_type.__name__
        if value is not None:
            tags.delall(frame_id)
            tags.add(frame_type(encoding=3, text=[str(value)]))
        elif clear_missing:
            tags.delall(frame_id)
    if values.get('comment') is not None:
        tags.delall('COMM')
        tags.add(COMM(encoding=3, lang='eng', desc='', text=[str(values['comment'])]))
    elif clear_missing:
        tags.delall('COMM')
    if values.get('asin') is not None:
        tags.delall('TXXX:ASIN')
        tags.add(TXXX(encoding=3, desc='ASIN', text=[str(values['asin'])]))
    elif clear_missing:
        tags.delall('TXXX:ASIN')
    if values.get('rating') is not None:
        tags.delall('POPM:calibre@local')
        tags.add(POPM(email='calibre@local', rating=max(0, min(255, int(float(values['rating']) * 51))), count=0))
    elif clear_missing:
        tags.delall('POPM:calibre@local')
    if values.get('cover') is not None:
        tags.delall('APIC')
        tags.add(APIC(encoding=3, mime=_image_mime(values['cover']), type=3, desc='Cover', data=values['cover']))
    elif clear_missing:
        tags.delall('APIC')
    tags.save(path, v2_version=3)


def write_m4b(path, values, clear_missing=False):
    audio = MP4(path)
    tags = audio.tags or {}
    audio.tags = tags
    for field, atom in MP4_KEYS.items():
        value = values.get(field)
        if value is not None:
            if atom.startswith('----:'):
                tags[atom] = [str(value).encode('utf-8')]
            else:
                tags[atom] = [str(value)]
        elif clear_missing:
            tags.pop(atom, None)
    if values.get('cover') is not None:
        image_format = MP4Cover.FORMAT_PNG if _is_png(values['cover']) else MP4Cover.FORMAT_JPEG
        tags['covr'] = [MP4Cover(values['cover'], imageformat=image_format)]
    elif clear_missing:
        tags.pop('covr', None)
    audio.save()


def write_audio(path, values, clear_missing=False, file_type=None):
    """Write to a filesystem path or a Calibre file stream.

    ``file_type`` is required for anonymous streams passed to a MetadataWriterPlugin.
    """
    extension = (file_type or str(path).rsplit('.', 1)[-1]).lower().lstrip('.')
    if extension == 'mp3':
        write_mp3(path, values, clear_missing)
    elif extension == 'm4b':
        write_m4b(path, values, clear_missing)
    else:
        raise ValueError('Unsupported audiobook format: {}'.format(extension))

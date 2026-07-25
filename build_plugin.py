"""Build a self-contained Calibre plugin ZIP with the Mutagen dependency vendored in."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).parent
ACTION_SOURCE = ROOT / 'calibre_plugin'
WRITER_SOURCE = ROOT / 'metadata_writer_plugin'
OUTPUTS = {
    'action': ROOT / 'dist' / 'AudnexusBulkAudiobookUpdate.zip',
    'writer': ROOT / 'dist' / 'AudnexusMetadataWriter.zip',
}


def add_tree(archive, source, destination=''):
    for path in source.rglob('*'):
        if path.is_file() and path.suffix not in ('.pyc', '.pyo'):
            archive.write(path, (Path(destination) / path.relative_to(source)).as_posix())


def build_zip(output, source, mutagen_dir, shared_source=None):
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        add_tree(archive, source)
        if shared_source:
            for filename in ('audio.py', 'metadata.py'):
                archive.write(shared_source / filename, filename)
        add_tree(archive, mutagen_dir, 'mutagen')


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        pip_command = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-compile', '--target', str(temp), 'mutagen>=1.47,<2']
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], check=True, stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            # Some embedded/distribution Pythons omit pip; uv is a compatible fallback.
            pip_command = ['uv', 'pip', 'install', '--python', sys.executable, '--no-compile', '--target', str(temp), 'mutagen>=1.47,<2']
        subprocess.run(pip_command, check=True)
        for output in OUTPUTS.values():
            output.parent.mkdir(exist_ok=True)
        build_zip(OUTPUTS['action'], ACTION_SOURCE, temp / 'mutagen')
        build_zip(OUTPUTS['writer'], WRITER_SOURCE, temp / 'mutagen', shared_source=ACTION_SOURCE)
    for output in OUTPUTS.values():
        print(output)


if __name__ == '__main__':
    main()

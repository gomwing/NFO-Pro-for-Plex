"""Map server library paths into a local metadata backup, without media files."""
import hashlib
import os
import re


def folder_name(value):
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value).rstrip(' .') or 'Library'
    if clean.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL'} | {f'{p}{i}' for p in ('COM', 'LPT') for i in range(1, 10)}:
        clean = '_' + clean
    if clean != value:
        clean += '-' + hashlib.sha256(value.encode()).hexdigest()[:8]
    return clean


def library_mappings(destination, sections):
    """Keep library root basenames; disambiguate equal names from distinct roots."""
    roots = sorted({str(r).replace('\\', '/').rstrip('/') for s in sections for r in s.locations})
    names = {r: folder_name(r.rsplit('/', 1)[-1] or 'Library') for r in roots}
    result = {}
    for r in roots:
        name = names[r]
        if sum(n.casefold() == name.casefold() for n in names.values()) > 1:
            name += '-' + hashlib.sha256(r.encode()).hexdigest()[:8]
        result[r] = os.path.join(destination, name)
    return result


def mapped_path(server_path, mappings):
    p = server_path.replace('\\', '/')
    for entry in sorted(mappings, key=lambda e: len(e.split(':||:', 1)[0]), reverse=True):
        source, target = entry.split(':||:', 1)
        source = source.replace('\\', '/').rstrip('/')
        # POSIX servers are case-sensitive, Windows paths are not.
        windows = bool(re.match(r'^[A-Za-z]:', source)) or source.startswith('//')
        left, right = (p.casefold(), source.casefold()) if windows else (p, source)
        if left != right and not left.startswith(right + '/'):
            continue
        parts = p[len(source):].strip('/').split('/')
        if any(part in ('.', '..') for part in parts):
            raise ValueError('Unsafe Plex path: ' + server_path)
        destination = os.path.realpath(target)
        result = os.path.realpath(os.path.join(destination, *(folder_name(x) for x in parts if x)))
        if os.path.commonpath([destination, result]) != destination:
            raise ValueError('Path escapes backup folder: ' + server_path)
        return result
    return None

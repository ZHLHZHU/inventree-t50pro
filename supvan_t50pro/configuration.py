"""Read printer definitions without depending on InvenTree."""
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse


def load_printers(path=None):
    explicit = path is not None or 'SUPVAN_PRINTER_CONFIG' in os.environ
    path = Path(path or os.environ.get(
        'SUPVAN_PRINTER_CONFIG', Path(__file__).with_name('printers.json')
    ))
    if not path.exists():
        if explicit:
            raise ValueError(f'Printer configuration does not exist: {path}')
        return [{'id': 'supvan-t50pro', 'name': '硕方 T50 Pro', 'uri': ''}]
    printers = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(printers, list) or not printers:
        raise ValueError('Printer configuration must be a non-empty JSON array')
    ids, names = set(), set()
    for printer in printers:
        if not isinstance(printer, dict):
            raise ValueError('Each printer must be an object')
        slug, name, uri = (printer.get(key) for key in ('id', 'name', 'uri'))
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError('Printer id must contain lowercase letters, digits and hyphens')
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Printer name must not be empty')
        if not isinstance(uri, str):
            raise ValueError('Printer uri must be a string')
        parsed = urlparse(uri)
        if (parsed.scheme != 'ipp' or not parsed.hostname
                or not parsed.path.startswith('/ipp/print/')
                or not parsed.path[len('/ipp/print/'):]
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError('Printer uri must be a complete ipp:// address')
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError('Printer uri port must be between 1 and 65535')
        if slug in ids or name in names:
            raise ValueError('Printer ids and names must be unique')
        ids.add(slug)
        names.add(name)
    return printers

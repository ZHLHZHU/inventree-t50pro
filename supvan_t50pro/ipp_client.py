"""Minimal IPP client: no retries for submissions, to avoid duplicate labels."""
import struct
import urllib.request
from urllib.parse import urlsplit, urlunsplit


def attribute(tag, name, value):
    name = name.encode('utf-8')
    if isinstance(value, int):
        value = struct.pack('>i', value)
    elif isinstance(value, str):
        value = value.encode('utf-8')
    return bytes([tag]) + struct.pack('>H', len(name)) + name + struct.pack('>H', len(value)) + value


def exchange(uri, operation, payload=b'', title='InvenTree label'):
    parsed = urlsplit(uri)
    if parsed.scheme not in ('ipp', 'ipps', 'http', 'https') or not parsed.hostname:
        raise ValueError('Invalid printer URI')
    http_scheme = 'https' if parsed.scheme in ('ipps', 'https') else 'http'
    target = urlunsplit((http_scheme, parsed.netloc, parsed.path, '', ''))
    ipp_uri = urlunsplit(('ipps' if http_scheme == 'https' else 'ipp', parsed.netloc, parsed.path, '', ''))
    body = struct.pack('>BBHI', 2, 0, operation, 1) + b'\x01'
    body += attribute(0x47, 'attributes-charset', 'utf-8')
    body += attribute(0x48, 'attributes-natural-language', 'en')
    body += attribute(0x45, 'printer-uri', ipp_uri)
    body += attribute(0x42, 'requesting-user-name', 'inventree')
    if operation == 2:
        body += attribute(0x42, 'job-name', title[:100])
        body += attribute(0x49, 'document-format', 'image/jpeg')
    body += b'\x03' + payload
    req = urllib.request.Request(target, data=body, headers={'Content-Type': 'application/ipp'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as response:
        result = response.read()
    if len(result) < 8:
        raise RuntimeError('Truncated IPP response')
    code = struct.unpack_from('>H', result, 2)[0]
    attrs = decode_attributes(result)
    if code > 0x00ff:
        raise RuntimeError(f"Printer rejected request (IPP {code:#06x}): {attrs.get('status-message', '')}")
    return attrs


def decode_attributes(data):
    offset = 8
    attrs = {}
    name = ''
    while offset < len(data):
        tag = data[offset]
        offset += 1
        if tag == 3:
            break
        if tag < 0x10:
            continue
        nlen = struct.unpack_from('>H', data, offset)[0]
        offset += 2
        if nlen:
            name = data[offset:offset+nlen].decode('utf-8', errors='replace')
        offset += nlen
        vlen = struct.unpack_from('>H', data, offset)[0]
        offset += 2
        value = data[offset:offset+vlen]
        offset += vlen
        if tag in (0x21, 0x23) and len(value) == 4:
            value = struct.unpack('>i', value)[0]
        elif tag in (0x41, 0x42, 0x44, 0x45, 0x47, 0x48, 0x49):
            value = value.decode('utf-8', errors='replace')
        attrs.setdefault(name, []).append(value)
    return attrs

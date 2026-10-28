#!/usr/bin/env python3
"""Validate the private build default without printing its URL."""
import hashlib
import os
import sys
from urllib.parse import unquote, urlsplit


def validate(value):
    try:
        url = urlsplit(value)
        local = url.hostname in ('localhost', '127.0.0.1', '::1')
        if value != value.strip() or not url.hostname or (url.scheme != 'https' and not (local and url.scheme == 'http')):
            raise ValueError()
        if url.username or url.password or url.query or url.fragment:
            raise ValueError()
        _ = url.port
        host = unquote(url.hostname).encode('idna').decode('ascii').lower().rstrip('.')
        official = ('bitwarden.com', 'bitwarden.eu', 'bitwarden.net', 'bitwarden.pw',
                    'bitwarden.services', 'bitwarden-gov.com', 'bitwarden.github.io')
        if any(host == domain or host.endswith('.' + domain) for domain in official):
            raise ValueError()
        if host == 'github.com' and (url.path.lower() == '/bitwarden' or url.path.lower().startswith('/bitwarden/')):
            raise ValueError()
    except ValueError:
        raise SystemExit('Invalid BW_DEFAULT_SERVER_URL: use a complete HTTPS base URL without credentials, query or fragment')
    return value.rstrip('/')


if __name__ == '__main__':
    value = os.environ.get('BW_DEFAULT_SERVER_URL', '')
    if not value:
        raise SystemExit('Set BW_DEFAULT_SERVER_URL in the ignored .env before building private clients')
    normalized = validate(value)
    if '--fingerprint' in sys.argv:
        print(hashlib.sha256(normalized.encode()).hexdigest())
    else:
        print('Private default server configuration verified')

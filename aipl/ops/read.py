from urllib.parse import urlparse, urlunparse

from aipl import defop, dbcache, stderr, alias


@dbcache
def _fetch_url_bytes(aipl, url:str) -> bytes:
    import urllib.request
    stderr(f'fetching {url}...')
    with urllib.request.urlopen(url) as resp:
        return resp.read()


@dbcache
def _fetch_url(aipl, url:str) -> str:
    import trafilatura
    stderr(f'fetching {url}...')
    # guess at decoding and other helpful things
    return trafilatura.fetch_url(url)


@defop('read', 0, 0)
def op_read(aipl, url:str) -> str:
    'Return contents of local filename.'
    if '://' in url:
        url = urlunparse(urlparse(url)._replace(fragment=''))
        return _fetch_url(aipl, url)

    return open(url).read()


@defop('read-bytes', 0, 0)
def op_read_bytes(aipl, url:str) -> bytes:
    'Return contents of URL or local filename as bytes.'
    if '://' in url:
        url = urlunparse(urlparse(url)._replace(fragment=''))
        return _fetch_url_bytes(url)

    return open(url, mode='rb').read()

alias('fetch-url', 'read')

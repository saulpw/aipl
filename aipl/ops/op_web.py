from typing import List, Dict
from urllib.parse import urljoin, urlparse, urlunparse

from aipl import defop, expensive, stderr


@defop('fetch-file', 0, 0, 1)
def op_fetch_file(aipl, fn:str) -> str:
    return open(fn).read()


@defop('fetch-url', 0, 0.5, 1)
@expensive
def op_fetch_url(aipl, url:str) -> dict:
    url = urlunparse(urlparse(url)._replace(fragment=''))

    stderr(f'fetching {url}...')

    import trafilatura
    return dict(url=url, contents=trafilatura.fetch_url(url))

@defop('fetch-url-bytes', 0, 0.5, 1)
@expensive
def op_fetch_url_bytes(aipl, url:str) -> dict:
    url = urlunparse(urlparse(url)._replace(fragment=''))

    stderr(f'fetching {url}...')

    import urllib.request
    with urllib.request.urlopen(url) as resp:
        return dict(url=url, contents=resp.read())


@defop('split-url', 0, 0.5)
def op_split_url(aipl, url:str) -> dict:
    r = urlparse(url)
    return dict(scheme=r.scheme,
               netloc=r.netloc,
               path=r.path,
               params=r.params,
               query=r.query,
               fragment=r.fragment)


@defop('defrag', 0, 0, 1)
def op_defrag(aipl, url:str) -> str:
    return urlunparse(urlparse(url)._replace(fragment=''))

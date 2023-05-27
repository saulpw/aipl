from typing import List, Dict
from urllib.parse import urljoin, urlparse, urlunparse

from aipl import defop, expensive, stderr


@defop('fetch-file', 0, 0, 1)
def op_fetch_file(aipl, fn:str) -> str:
    return open(fn).read()


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

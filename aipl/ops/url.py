from urllib.parse import urlparse, urlunparse

from aipl import defop


@defop('url-split', 0, 0.5)
def op_url_split(aipl, url:str) -> dict:
    'Split url into components (scheme, netloc, path, params, query, fragment).'
    r = urlparse(url)
    return dict(scheme=r.scheme,
               netloc=r.netloc,
               path=r.path,
               params=r.params,
               query=r.query,
               fragment=r.fragment)


@defop('url-defrag', 0, 0, 1)
def op_url_defrag(aipl, url:str) -> str:
    'Remove fragment from url.'
    return urlunparse(urlparse(url)._replace(fragment=''))

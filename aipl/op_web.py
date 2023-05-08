from typing import List, Dict
from urllib.parse import urljoin, urlparse, urlunparse

from .interpreter import defop, expensive
from .utils import stderr


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


@defop('extract-text', 0, 0, 1)
def op_extract_text(aipl, html:str, **kwargs) -> str:
    'Extract text from HTML'
    parms = dict(include_comments=False,
                 include_tables=False,
                 no_fallback=True)
    parms.update(kwargs)

    import trafilatura
    return trafilatura.extract(html, **parms)


@defop('extract-links', 0, 1.5)
def op_extract_links(aipl, html:str, baseurl='', **kwargs) -> List[dict]:
    'Extract links (href attribute from <a> tags) from HTML'
    if not html:
        return

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        if baseurl:
            href = urljoin(baseurl, href)
        yield dict(linktext=link.text, title=link.get('title', ''), href=href)


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

from typing import List
from urllib.parse import urljoin

from aipl import defop


@defop('extract-text-all', 0, 0, 1)
def op_extract_text_all(aipl, html:str, **kwargs) -> str:
    'Extract all text from HTML'
    import trafilatura
    return trafilatura.html2txt(html, **kwargs)


@defop('extract-text', 0, 0, 1)
def op_extract_text(aipl, html:str, **kwargs) -> str:
    'Extract meaningful text from HTML'
    parms = dict(include_comments=False,
                 include_tables=False,
                 no_fallback=True)
    parms.update(kwargs)

    import trafilatura
    content = trafilatura.extract(html, **parms)
    if content is None:
        return ''
    else:
        return content


@defop('extract-links', 0, 1.5, outcols='linktext title href')
def op_extract_links(aipl, html:str, baseurl='', **kwargs) -> List[dict]:
    'Extract (linktext, title, href) from <a> tags in HTML'
    if not html:
        return

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        if baseurl:
            href = urljoin(baseurl, href)
        yield dict(linktext=link.text, title=link.get('title', ''), href=href)

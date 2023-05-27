from aipl import defop, expensive, stderr


@defop('fetch-url', 0, 0.5, 1)
@expensive
def op_fetch_url(aipl, url:str) -> dict:
    'Fetch URL as text.'
    url = urlunparse(urlparse(url)._replace(fragment=''))

    stderr(f'fetching {url}...')

    import trafilatura
    return dict(url=url, contents=trafilatura.fetch_url(url))


@defop('fetch-url-bytes', 0, 0.5, 1)
@expensive
def op_fetch_url_bytes(aipl, url:str) -> dict:
    'Fetch URL as raw bytes.'
    url = urlunparse(urlparse(url)._replace(fragment=''))

    stderr(f'fetching {url}...')

    import urllib.request
    with urllib.request.urlopen(url) as resp:
        return dict(url=url, contents=resp.read())

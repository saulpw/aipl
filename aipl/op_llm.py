from typing import List, Dict

from .utils import stderr
from . import defop, expensive


def _parse_msg(s:str):
    if s.startswith('@@@s'):
        return dict(role='system', content=s)
    elif s.startswith('@@@a'):
        return dict(role='assistant', content=s)
    else:  # if s.startswith('@@@u'):
        return dict(role='user', content=s)


@defop('llm', 0, 0, 1)
@expensive
def op_llm(aipl, v:str, **kwargs) -> str:
    import openai
    parms = dict(
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    parms.update(kwargs)
    msgs = [_parse_msg(m) for m in v.splitlines()]

    resp = openai.ChatCompletion.create(
        messages=msgs,
        **parms
    )
    used = resp['usage']['total_tokens']
    stderr(f'Used {used} tokens')
    return resp['choices'][0]['message']['content']


@defop('llm-embedding', 0, 0, 1)
@expensive
def op_llm_embedding(aipl, v:str, **kwargs) -> List[float]:
    import openai

    if not v:
        raise Exception('no content for embedding')

    resp = openai.Embedding.create(input=v, **kwargs)

    used = resp['usage']['total_tokens']
    stderr(f'Used {used} tokens')

    return resp['data'][0]['embedding']


@defop('cluster', 1, 1, 1)
def op_cluster(aipl, v:List[List[float]], n=10):
    'Find n clusters in the input vectors'
    import numpy as np
    from sklearn.cluster import KMeans

    matrix = np.vstack(v)
    kmeans = KMeans(n_clusters=n, init='k-means++', random_state=42, n_init='auto')
    kmeans.fit(matrix)

    return [int(x) for x in kmeans.labels_]

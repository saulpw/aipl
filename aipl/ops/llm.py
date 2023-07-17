'''
!llm and !llm-embedding use the OpenAI API to make queries to GPT.

Requires OPENAI_API_KEY and OPENAI_API_ORG envvars to be set.
'''

from typing import List, Dict
import os
import subprocess
from pathlib import Path

from aipl import defop, expensive, stderr, AIPLException, clients


def _parse_msg(s:str):
    if s.startswith('@@@s'):
        return dict(role='system', content=s)
    elif s.startswith('@@@a'):
        return dict(role='assistant', content=s)
    else:  # if s.startswith('@@@u'):
        return dict(role='user', content=s)

def op_llm_mock(aipl, v:str, **kwargs) -> str:
    model = kwargs.get('model')
    used = clients.count_tokens(v, model=model)
    cost = clients.openai_pricing[model]*used/1000
    aipl.cost_usd += cost
    return f'<llm {model} answer>'

@defop('llm', 0, 0)
@expensive(op_llm_mock)
def route_llm_query(aipl, v:str, **kwargs) -> str:
    'Send chat messages to `model` (default: gpt-3.5-turbo).  Lines beginning with @@@s or @@@a are sent as system or assistant messages respectively (default user).  Passes all named args directly to API.'
    client_str = kwargs.get('client')
    if client_str is None:
        if os.environ['LLM_CLIENT_ENDPOINT']:
            client = clients.SelfHostedChatClient()
        else:
            client = clients.OpenAIClient()
    else:
        if client_str == 'selfhosted':
            client = clients.SelfHostedChatClient()
        elif client_str == 'openai':
            client = clients.OpenAIClient()
        elif client_str == 'gooseai':
            client = clients.GooseClient()
        else:
            raise AIPLException(f"client '{client_str}' not recognized")

    return client.completion(aipl, v, **kwargs)

@defop('llm-embedding', 0, 0.5)
@expensive()
def route_llm_embedding_query(aipl, v:str, **kwargs) -> str:
    'Get a [text embedding](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings) for a string from `model`: a measure of text-relatedness, to be used with e.g. !cluster.'
    model = kwargs.get('model')
    if model in clients.gooseai_models:
        raise AIPLException("GooseAI embeddings not yet supported")
    elif model in clients.openai_pricing:
        return embedding_openai(aipl, v, **kwargs)
    else:
        raise AIPLException(f"{model} not found!")

def embedding_openai(aipl, v:str, **kwargs) -> dict:
    'Get a an openai [text embedding](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings) for a string: a measure of text-relatedness, to be used with e.g. !cluster.'
    import openai

    if not v:
        raise Exception('no content for embedding')

    if 'OPENAI_API_KEY' not in os.environ or 'OPENAI_API_ORG' not in os.environ:
        raise AIPLException('''OPENAI_API_KEY and OPENAI_API_ORG envvars must be set for !llm''')

    resp = openai.Embedding.create(input=v, **kwargs)

    used = resp['usage']['total_tokens']
    stderr(f'Used {used} tokens')

    return dict(model=kwargs.get('model'),
                used_tokens=used,
                embedding=resp['data'][0]['embedding'])
'''
!llm and !llm-embedding use the OpenAI API to make queries to GPT.

Requires OPENAI_API_KEY and OPENAI_API_ORG envvars to be set.
'''

from typing import List, Dict
import os

from aipl import defop, expensive, stderr, AIPLException


def _parse_msg(s:str):
    if s.startswith('@@@s'):
        return dict(role='system', content=s)
    elif s.startswith('@@@a'):
        return dict(role='assistant', content=s)
    else:  # if s.startswith('@@@u'):
        return dict(role='user', content=s)


# from the horse's mouth, 2023-05-30
openai_pricing = {
    "gpt-4": 0.06,
    "gpt-4-32k": 0.12,
    "gpt-3.5-turbo": 0.002,
    "text-ada-001": 0.0016,
    "text-babbage-001": 0.0024,
    "text-curie-001": 0.0120,
    "text-davinci-003": 0.1200
}

# base price covers the first 25 tokens, then it's the per-token price (2023-06-06)
gooseai_pricing = {
    "fairseq-13b": {
        "base": 0.001250,
        "token": 0.000036
    },
    "gpt-neo-20b": {
        "base": 0.002650, 
        "token": 0.000063
    }
}

def count_tokens(s:str, model:str=''):
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(s))
    except ModuleNotFoundError as e:
#        stderr(str(e))
        return len(s)//4


def op_llm_mock(aipl, v:str, **kwargs) -> str:
    model = kwargs.get('model')
    used = count_tokens(v, model=model)
    cost = openai_pricing[model]*used/1000
    aipl.cost_usd += cost
    return f'<llm {model} answer>'

@defop('llm', 0, 0, 1)
@expensive(op_llm_mock)
def route_llm_query(aipl, v:str, **kwargs) -> str:
    model = kwargs.get('model')
    if model in gooseai_pricing:
        return completion_gooseai(aipl, v, **kwargs)
    elif model in openai_pricing:
        return completion_openai(aipl, v, **kwargs)
    else:
        raise AIPLException(f"{model} not found!")

def completion_openai(aipl, v:str, **kwargs) -> str:
    'Send chat messages to GPT.  Lines beginning with @@@s or @@@a are sent as system or assistant messages respectively (default user).  Passes all [named args](https://platform.openai.com/docs/guides/chat/introduction) directly to API.'
    import openai
    model = kwargs.get('model')
    parms = dict(
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    parms.update(kwargs)
    msgs = [_parse_msg(m) for m in v.splitlines()]

    if 'OPENAI_API_KEY' not in os.environ or 'OPENAI_API_ORG' not in os.environ:
        raise AIPLException('''OPENAI_API_KEY and OPENAI_API_ORG envvars must be set for !llm''')

    resp = openai.ChatCompletion.create(
        messages=msgs,
        **parms
    )
    used = resp['usage']['total_tokens']
    result = resp['choices'][0]['message']['content']

    cost = openai_pricing[model]*used/1000
    aipl.cost_usd += cost
    stderr(f'Used {used} tokens (estimate {len(v)//4} tokens).  Cost: ${cost:.02f}')
    return result

def completion_gooseai(aipl, v:str, **kwargs) -> str:
    import requests
    model = kwargs.get('model')
    if 'GOOSE_AI_KEY' not in os.environ:
        raise AIPLException(f'''GOOSE_AI_KEY envvar must be set for !llm to use {model}''')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ["GOOSE_AI_KEY"]}'
    }
    params = dict(
        temperature=0
    )
    params.update(**kwargs)
    # TODO: GooseAI supports multiple prompt completions in parallel
    data = {'prompt': v, **params}
    r = requests.post(f'https://api.goose.ai/v1/engines/{model}/completions', headers=headers, json=data)
    j = r.json()
    if 'error' in j:
        raise AIPLException(f'''GooseAI returned an error: {j["error"]}''')
    # TODO: GooseAI does not return number of tokens used, so we would need to use a tokenizer library to compute that separately
    # (also note that some of their models don't use the gpt2 tokenizer either, so we'd need to store that data too)
    return j['choices'][0]['text']

@defop('llm-embedding', 0, 0.5, 1)
@expensive()
def route_llm_embedding_query(aipl, v:str, **kwargs) -> str:
    model = kwargs.get('model')
    if model in gooseai_pricing:
        raise AIPLException("GooseAI models not yet supported")
    elif model in openai_pricing:
        return embedding_openai(aipl, v, **kwargs)
    else:
        raise AIPLException(f"{model} not found!")
    
def embedding_openai(aipl, v:str, **kwargs) -> dict:
    'Get a [text embedding](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings) for a string: a measure of text-relatedness, to be used with e.g. !cluster.'
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

'''
!llm and !llm-embedding use the OpenAI API
to make queries to their llm models.

Require the setting of an OPENAI_API_KEY.
'''

from typing import List, Dict

from aipl import defop, expensive, stderr


def _parse_msg(s:str):
    if s.startswith('@@@s'):
        return dict(role='system', content=s)
    elif s.startswith('@@@a'):
        return dict(role='assistant', content=s)
    else:  # if s.startswith('@@@u'):
        return dict(role='user', content=s)


# from the horse's mouth, 2023-05-30
openai_pricing = {
    "gpt-4-8k": 0.06,
    "gpt-4-32k": 0.12,
    "gpt-3.5-turbo": 0.002,
    "ada": 0.0016,
    "babbage": 0.0024,
    "curie": 0.0120,
    "davinci": 0.1200
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
def op_llm(aipl, v:str, **kwargs) -> str:
    'Send a chat message to an OpenAI LLM. Supports [all params](https://platform.openai.com/docs/guides/chat/introduction).'
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


@defop('llm-embedding', 0, 0.5, 1)
@expensive()
def op_llm_embedding(aipl, v:str, **kwargs) -> dict:
    'Get a [text embedding](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings) for a string: a measure of text-relatedness, to be used with e.g. !cluster.'
    import openai

    if not v:
        raise Exception('no content for embedding')

    resp = openai.Embedding.create(input=v, **kwargs)

    used = resp['usage']['total_tokens']
    stderr(f'Used {used} tokens')

    return dict(model=kwargs.get('model'),
                used_tokens=used,
                embedding=resp['data'][0]['embedding'])

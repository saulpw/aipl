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


@defop('llm', 0, 0, 1)
@expensive
def op_llm(aipl, v:str, **kwargs) -> str:
    'Send a chat message to an OpenAI LLM. Supports [all params](https://platform.openai.com/docs/guides/chat/introduction).'
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


@defop('llm-embedding', 0, 0.5, 1)
@expensive
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

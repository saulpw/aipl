from aipl import defop, expensive, stderr, AIPLException
import openai
import os

# from the horse's mouth, 2023-05-30
openai_pricing = {
    "gpt-4": 0.06,
    "gpt-4-32k": 0.12,
    "gpt-3.5-turbo": 0.002,
    "gpt-3.5-turbo-16k": 0.002,
    "text-ada-001": 0.0016,
    "text-babbage-001": 0.0024,
    "text-curie-001": 0.0120,
    "text-davinci-003": 0.1200
}

# base price covers the first 25 tokens, then it's the per-token price (2023-06-06)
gooseai_models = {
    "fairseq-13b": {
        "pricing": {
            "base": 0.001250,
            "token": 0.000036
        },
        "encoding": ""
    },
    "gpt-neo-20b": {
        "pricing": {
            "base": 0.002650, 
            "token": 0.000063
        },
        "encoding": "gpt2"
    }
}

def _parse_msg(s:str):
    if s.startswith('@@@s'):
        return dict(role='system', content=s)
    elif s.startswith('@@@a'):
        return dict(role='assistant', content=s)
    else:  # if s.startswith('@@@u'):
        return dict(role='user', content=s)


def count_tokens(s:str, model:str=''):
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(s))
    except ModuleNotFoundError as e:
#        stderr(str(e))
        return len(s)//4
    except KeyError as e:
        # just estimate
        return len(s)//4


class StandardClient:
    def compute_cost(self, aipl, resp, model):
        if self.client_type == 'openai':
            used = resp['usage']['total_tokens']
            result = resp['choices'][0]['message']['content']
            cost = openai_pricing[model]*used/1000
            if aipl: # makes it easier to run unit tests
                aipl.cost_usd += cost

            stderr(f'Used {used} tokens (estimate {len(result)//4} tokens).  Cost: ${cost:.03f}')
        elif self.client_type == 'selfhosted':
            stderr('Used TODO tokens. Cost: $¯\_(ツ)_/¯')

    def completion(self, aipl, v:str, **kwargs) -> str:
        'Send chat messages to GPT.  Lines beginning with @@@s or @@@a are sent as system or assistant messages respectively (default user).  Passes all [named args](https://platform.openai.com/docs/guides/chat/introduction) directly to API.'
        model = kwargs.get('model') or self.default_model
        temperature = kwargs.get('temperature') or 0
        params = dict(
            temperature=float(temperature),
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            model=model
        )
        params.update(kwargs)

        # TODO: there must be a less hacky way of doing these
        params['temperature'] = float(params['temperature'])
        if 'client' in params:
            del params['client']

        # msgs = [_parse_msg(m) for m in v.splitlines()]
        msgs = [_parse_msg(v)]

        resp = openai.ChatCompletion.create(
            messages=msgs,
            **params
        )
        try:
            result = resp['choices'][0]['message']['content']
        except:
            raise AIPLException(resp)
        self.compute_cost(aipl, resp, model)

        return result


class GooseClient(StandardClient):
    def __init__(self):
        if 'GOOSE_AI_KEY' not in os.environ:
            raise AIPLException(f'''GOOSE_AI_KEY envvar must be set to use gooseai client type''')
        self.client_type = 'gooseai'
        self.default_model = 'gpt-neo-20b'
        openai.api_key = os.environ['GOOSE_AI_KEY']
        openai.api_base = "https://api.goose.ai/v1"

    def completion(self, aipl, v, **kwargs):
        import requests

        model = kwargs.get('model') or self.default_model
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

        response = j['choices'][0]['text']
        # Only output tokens are charged
        used = count_tokens(response, gooseai_models[model]['encoding'])
        # GooseAI's base cost provides the first 25 tokens, then each token after is charged at the token rate
        cost = gooseai_models[model]['pricing']['token'] * max(0, used-25) + gooseai_models[model]['pricing']['base']
        if aipl:
            aipl.cost_usd += cost
        stderr(f'Used {used} tokens (estimate {len(v)//4} tokens).  Cost: ${cost:.03f}')
        return response


class OpenAIClient(StandardClient):
    def __init__(self):
        if 'OPENAI_API_KEY' not in os.environ or 'OPENAI_API_ORG' not in os.environ:
            raise AIPLException('''OPENAI_API_KEY and OPENAI_API_ORG envvars must be set for openai client type''')
        self.client_type = 'openai'
        self.default_model = 'gpt-3.5-turbo'


class SelfHostedChatClient(StandardClient):
    def __init__(self):
        if 'LLM_CLIENT_ENDPOINT' not in os.environ:
            raise AIPLException('''LLM_CLIENT_ENDPOINT envvar must be set for selfhosted client type''')
        openai.api_base = os.environ['LLM_CLIENT_ENDPOINT']
        self.client_type = 'selfhosted'
        if 'DEFAULT_SELFHOSTED_MODEL' in os.environ:
            self.default_model = os.environ['DEFAULT_SELFHOSTED_MODEL']


if __name__ == "__main__":
    max_tokens = 10
    prompt = '''A lesser-known robot character from sci-fi is'''

    print('openai\n', prompt, OpenAIClient().completion(None, prompt, max_tokens=max_tokens))
    print('gooseai\n', prompt, GooseClient().completion(None, prompt, max_tokens=max_tokens))
    print('selfhosted\n', prompt, SelfHostedChatClient().completion(None, prompt, max_tokens=max_tokens))

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

class StandardClient:
    def __init__(self, base_url=None):
        if base_url:
            print("using", base_url)
            openai.api_base = base_url
    
    def compute_cost(self, aipl, resp, model):
        if self.type == 'openai':
            used = resp['usage']['total_tokens']
            result = resp['choices'][0]['message']['content']
            cost = openai_pricing[model]*used/1000
            if aipl: # makes it easier to run unit tests
                aipl.cost_usd += cost

            stderr(f'Used {used} tokens (estimate {len(result)//4} tokens).  Cost: ${cost:.03f}')
        elif self.type == 'custom':
            stderr('Used TODO tokens. Cost: $¯\_(ツ)_/¯')
    
    def completion(self, aipl, v:str, **kwargs) -> str:
        'Send chat messages to GPT.  Lines beginning with @@@s or @@@a are sent as system or assistant messages respectively (default user).  Passes all [named args](https://platform.openai.com/docs/guides/chat/introduction) directly to API.'
        model = kwargs.get('model') or self.default_model
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
        self.type = 'gooseai'
        self.default_model = 'gpt-neox-20b'
        super().__init__(f'https://api.goose.ai/v1/engines/')

class OpenAIClient(StandardClient):
    def __init__(self):
        if 'OPENAI_API_KEY' not in os.environ or 'OPENAI_API_ORG' not in os.environ:
            raise AIPLException('''OPENAI_API_KEY and OPENAI_API_ORG envvars must be set for openai client type''')
        self.type = 'openai'
        self.default_model = 'gpt-3.5-turbo'
        super().__init__()

class SelfHostedChatClient(StandardClient):
    def __init__(self):
        if 'LLM_CLIENT_ENDPOINT' not in os.environ:
            raise AIPLException('''LLM_CLIENT_ENDPOINT envvar must be set for selfhosted client type''')
        self.type = 'selfhosted'
        super().__init__(os.environ['LLM_CLIENT_ENDPOINT'])

if __name__ == "__main__":
    prompt = "At this rate, George RR Martin will release The Winds of Winter when"

    # print('openai\n', prompt, OpenAIClient().completion(None, prompt, model='gpt-3.5-turbo'))
    # print('gooseai\n', prompt, GooseClient().completion(None, prompt))
    print('selfhosted\n', prompt, SelfHostedChatClient().completion(None, prompt, model='Aeala/VicUnlocked-alpaca-30b-ggml/VicUnlocked-alpaca-30b-q4_0.bin', max_tokens=32))
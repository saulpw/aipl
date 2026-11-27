import pytest

from aipl import clients
from aipl.ops import llm


def chat_response(prompt_tokens, completion_tokens):
    return {
        'choices': [{'message': {'content': 'answer'}}],
        'usage': {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
        },
    }


def openai_client():
    client = clients.StandardClient()
    client.client_type = 'openai'
    return client


def test_openai_cost_prices_input_and_output_separately():
    # gpt-4: $0.03/1K input, $0.06/1K output
    assert clients.openai_cost('gpt-4', 1000, 0) == pytest.approx(0.03)
    assert clients.openai_cost('gpt-4', 0, 1000) == pytest.approx(0.06)
    assert clients.openai_cost('gpt-4', 2000, 500) == pytest.approx(0.09)


def test_openai_cost_unknown_model():
    assert clients.openai_cost('no-such-model', 1000, 1000) is None


def test_compute_cost_uses_prompt_and_completion_tokens(aipl):
    openai_client().compute_cost(aipl, chat_response(1000, 500), 'gpt-4')
    assert aipl.cost_usd == pytest.approx(0.03 + 0.03)


def test_compute_cost_unknown_model_keeps_response(aipl):
    openai_client().compute_cost(aipl, chat_response(1000, 500), 'gpt-unknown')
    assert aipl.cost_usd == 0


def test_dry_run_estimate_uses_max_tokens(aipl):
    prompt = 'x' * 4000  # 1000 tokens with the len//4 estimate
    prompt_tokens = clients.count_tokens(prompt, model='gpt-4')
    llm.op_llm_mock(aipl, prompt, model='gpt-4', max_tokens='100')
    assert aipl.cost_usd == pytest.approx((0.03*prompt_tokens + 0.06*100)/1000)


def test_dry_run_estimate_without_max_tokens(aipl):
    prompt = 'x' * 4000
    prompt_tokens = clients.count_tokens(prompt, model='gpt-4')
    llm.op_llm_mock(aipl, prompt, model='gpt-4')
    assert aipl.cost_usd == pytest.approx((0.03 + 0.06)*prompt_tokens/1000)


def test_dry_run_default_model(aipl):
    assert llm.op_llm_mock(aipl, 'hello') == f'<llm {clients.DEFAULT_OPENAI_MODEL} answer>'
    assert aipl.cost_usd > 0


def test_dry_run_unknown_model(aipl):
    llm.op_llm_mock(aipl, 'hello', model='some-selfhosted-model')
    assert aipl.cost_usd == 0


def test_embedding_cost(aipl, monkeypatch):
    import openai
    monkeypatch.setenv('OPENAI_API_KEY', 'test')
    monkeypatch.setenv('OPENAI_API_ORG', 'test')
    monkeypatch.setattr(openai.Embedding, 'create', lambda **kwargs: {
        'usage': {'prompt_tokens': 1000, 'total_tokens': 1000},
        'data': [{'embedding': [0.1, 0.2]}],
    })
    ret = llm.route_llm_embedding_query(aipl, 'hello', model='text-embedding-ada-002')
    assert ret['used_tokens'] == 1000
    assert aipl.cost_usd == pytest.approx(0.0001)

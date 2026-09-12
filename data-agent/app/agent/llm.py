from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

def _create_model(model_name: str):
    return init_chat_model(
        model=model_name,
        model_provider="openai",
        api_key=app_config.llm.api_key,
        base_url=app_config.llm.base_url,
        temperature=0,
        timeout=app_config.llm.timeout_seconds,
        max_retries=app_config.llm.max_retries,
    )


fast_model_name = app_config.llm.fast_model_name or app_config.llm.model_name
reasoning_model_name = (
    app_config.llm.reasoning_model_name or app_config.llm.model_name
)

fast_llm = _create_model(fast_model_name)
reasoning_llm = (
    fast_llm
    if reasoning_model_name == fast_model_name
    else _create_model(reasoning_model_name)
)

# Backwards-compatible alias for small scripts importing the old symbol.
llm = reasoning_llm


if __name__ == '__main__':
    for chunk in llm.stream("What is the meaning of life?"):
        print(chunk.text)

from langchain_openai import ChatOpenAI

from src.config import get_settings


def get_llm() -> ChatOpenAI:
    settings = get_settings()
    api_key = settings.qwen_api_key
    base_url = settings.qwen_api_base
    return ChatOpenAI(
        model=settings.model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=settings.llm_temperature,
    )

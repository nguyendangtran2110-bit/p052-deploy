from langchain_openai import ChatOpenAI

from src.config import get_settings


def _has_usable_api_key(api_key: str) -> bool:
    key = api_key.strip()
    if not key or key.startswith("your-"):
        return False
    return key.isascii()


def get_llm():
    settings = get_settings()

    qwen_api_key = settings.qwen_api_key or settings.openai_api_key
    qwen_base_url = settings.qwen_api_base or settings.openai_api_base
    qwen_llm = None
    if _has_usable_api_key(qwen_api_key):
        qwen_llm = ChatOpenAI(
            model=settings.qwen_model_name,
            api_key=qwen_api_key,
            base_url=qwen_base_url,
            temperature=settings.llm_temperature,
        )

    if not _has_usable_api_key(settings.groq_api_key):
        if qwen_llm is None:
            raise RuntimeError("Missing valid GROQ_API_KEY and QWEN_API_KEY for LLM configuration")
        return qwen_llm

    groq_llm = ChatOpenAI(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        base_url=settings.groq_api_base,
        temperature=settings.llm_temperature,
    )

    if qwen_llm is None:
        return groq_llm
    return groq_llm.with_fallbacks([qwen_llm])

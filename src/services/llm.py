from langchain_openai import ChatOpenAI

from src.config import get_settings


def _has_usable_api_key(api_key: str) -> bool:
    key = api_key.strip()
    if not key or key.startswith("your-"):
        return False
    return key.isascii()


def get_llm():
    settings = get_settings()

    llms = []
    if _has_usable_api_key(settings.openai_api_key):
        llms.append(
            ChatOpenAI(
                model=settings.model_name,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
                temperature=settings.llm_temperature,
            )
        )

    if _has_usable_api_key(settings.qwen_api_key):
        llms.append(
            ChatOpenAI(
                model=settings.qwen_model_name,
                api_key=settings.qwen_api_key,
                base_url=settings.qwen_api_base,
                temperature=settings.llm_temperature,
            )
        )

    if _has_usable_api_key(settings.groq_api_key):
        llms.append(
            ChatOpenAI(
                model=settings.groq_model_name,
                api_key=settings.groq_api_key,
                base_url=settings.groq_api_base,
                temperature=settings.llm_temperature,
            )
        )

    if not llms:
        raise RuntimeError("Missing valid OPENAI_API_KEY, QWEN_API_KEY, or GROQ_API_KEY for LLM configuration")

    primary, *fallbacks = llms
    if not fallbacks:
        return primary
    return primary.with_fallbacks(fallbacks)

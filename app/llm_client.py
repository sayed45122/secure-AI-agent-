import os
from typing import Any, Dict, List, Optional

try:
    from groq import Groq
except Exception as exc:
    Groq = None
    _GROQ_IMPORT_ERROR = exc
else:
    _GROQ_IMPORT_ERROR = None

try:
    import streamlit as st
except Exception:
    st = None


DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _get_api_key() -> Optional[str]:
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key

    if st is not None:
        try:
            key = st.secrets.get("GROQ_API_KEY")
            if key:
                return key
        except Exception:
            pass

    return None


def has_groq_api_key() -> bool:
    return bool(_get_api_key())


def get_groq_client() -> "Groq":
    if Groq is None:
        raise ImportError(
            "The 'groq' package is not installed correctly."
        ) from _GROQ_IMPORT_ERROR

    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set.\n"
            "Set it locally with:\n"
            "export GROQ_API_KEY='your_key'\n"
            "Or add it in Streamlit secrets."
        )

    return Groq(api_key=api_key)


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> Any:
    client = get_groq_client()
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response


def generate_text(
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> str:
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    response = chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content


class LLMClient:
    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.client = get_groq_client()

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )


# compatibility aliases
get_client = get_groq_client
ask_llm = generate_text
complete = generate_text

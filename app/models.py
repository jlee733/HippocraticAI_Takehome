import os
from typing import Callable

import openai
import requests

DEFAULT_GEMMA_MODEL = "gemma2:2b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
OPENAI_MODEL = "gpt-3.5-turbo"

MODEL_GPT = "gpt-3.5-turbo"
MODEL_GEMMA = "gemma"

MODEL_CHOICES = [MODEL_GPT, MODEL_GEMMA]


def chat_openai(
    messages: list[dict[str, str]],
    max_tokens: int = 3000,
    temperature: float = 0.7,
) -> str:
    """Send a multi-turn conversation to OpenAI."""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=messages,
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message["content"]  # type: ignore


def chat_gemma(
    messages: list[dict[str, str]],
    max_tokens: int = 3000,
    temperature: float = 0.7,
) -> str:
    """Send a multi-turn conversation to Gemma via Ollama."""
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    model = os.getenv("GEMMA_MODEL", DEFAULT_GEMMA_MODEL)

    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def chat_with_model(
    model_name: str,
    messages: list[dict[str, str]],
    max_tokens: int = 3000,
    temperature: float = 0.7,
) -> str:
    """Send a conversation to the selected model."""
    if model_name == MODEL_GEMMA:
        return chat_gemma(messages, max_tokens=max_tokens, temperature=temperature)
    if model_name == MODEL_GPT:
        return chat_openai(messages, max_tokens=max_tokens, temperature=temperature)
    raise ValueError(f"Unsupported model: {model_name}")


def call_gemma(
    prompt: str,
    max_tokens: int = 3000,
    temperature: float = 0.1,
) -> str:
    """Call a Gemma model served locally via Ollama."""
    return chat_gemma(
        [{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )


MODEL_OPTIONS = {
    MODEL_GPT: {
        "label": "gpt-3.5-turbo (OpenAI)",
        "description": "Requires OPENAI_API_KEY",
    },
    MODEL_GEMMA: {
        "label": "gemma (open-source via Ollama)",
        "description": "Uses Gemma via Ollama (bundled when running in Docker)",
    },
}


def get_model_fn(model_name: str, openai_fn: Callable[[str], str]) -> Callable[[str], str]:
    """Return the callable for the selected model."""
    if model_name == MODEL_GEMMA:
        return call_gemma
    if model_name == MODEL_GPT:
        return openai_fn
    raise ValueError(f"Unsupported model: {model_name}")


def resolve_model_name(model_name: str | None = None) -> str:
    """Resolve model from argument, env var, or interactive prompt."""
    if model_name:
        normalized = model_name.strip().lower()
        if normalized in {MODEL_GPT, "1", "openai", "gpt"}:
            return MODEL_GPT
        if normalized in {MODEL_GEMMA, "2", "ollama"}:
            return MODEL_GEMMA
        raise ValueError(f"Unsupported model: {model_name}")

    env_model = os.getenv("STORY_MODEL", "").strip().lower()
    if env_model:
        return resolve_model_name(env_model)

    return prompt_model_selection()


def prompt_model_selection() -> str:
    """Ask the user which model to use."""
    print("\nChoose a model:")
    print(f"  1. {MODEL_OPTIONS[MODEL_GPT]['label']}")
    print(f"     {MODEL_OPTIONS[MODEL_GPT]['description']}")
    print(f"  2. {MODEL_OPTIONS[MODEL_GEMMA]['label']}")
    print(f"     {MODEL_OPTIONS[MODEL_GEMMA]['description']}")

    choice = input("\nEnter 1 or 2 [default: 1]: ").strip()
    if choice in {"", "1"}:
        return MODEL_GPT
    if choice == "2":
        return MODEL_GEMMA
    raise ValueError("Invalid model choice. Enter 1 or 2.")

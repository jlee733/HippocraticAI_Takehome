from unittest.mock import MagicMock, patch

import pytest
import requests

from app.models import (
    MODEL_GEMMA,
    MODEL_GPT,
    call_gemma,
    chat_gemma,
    chat_openai,
    chat_with_model,
    get_model_fn,
    prompt_model_selection,
    resolve_model_name,
)


class TestResolveModelName:
    def test_resolves_gpt_aliases(self):
        assert resolve_model_name("gpt-3.5-turbo") == MODEL_GPT
        assert resolve_model_name("openai") == MODEL_GPT
        assert resolve_model_name("1") == MODEL_GPT

    def test_resolves_gemma_aliases(self):
        assert resolve_model_name("gemma") == MODEL_GEMMA
        assert resolve_model_name("ollama") == MODEL_GEMMA
        assert resolve_model_name("2") == MODEL_GEMMA

    def test_raises_for_unknown_model(self):
        with pytest.raises(ValueError, match="Unsupported model"):
            resolve_model_name("llama")

    @patch.dict("os.environ", {"STORY_MODEL": "gemma"})
    def test_reads_model_from_env(self):
        assert resolve_model_name() == MODEL_GEMMA


class TestPromptModelSelection:
    @patch("builtins.input", return_value="")
    def test_defaults_to_gpt(self, _mock_input):
        assert prompt_model_selection() == MODEL_GPT

    @patch("builtins.input", return_value="2")
    def test_selects_gemma(self, _mock_input):
        assert prompt_model_selection() == MODEL_GEMMA

    @patch("builtins.input", return_value="9")
    def test_rejects_invalid_choice(self, _mock_input):
        with pytest.raises(ValueError, match="Invalid model choice"):
            prompt_model_selection()


class TestGetModelFn:
    def test_returns_openai_fn_for_gpt(self):
        openai_fn = MagicMock()
        assert get_model_fn(MODEL_GPT, openai_fn) is openai_fn

    def test_returns_gemma_fn_for_gemma(self):
        openai_fn = MagicMock()
        assert get_model_fn(MODEL_GEMMA, openai_fn) is call_gemma


class TestCallGemma:
    @patch("app.models.requests.post")
    def test_calls_ollama_chat_api(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Gemma story."}}
        mock_post.return_value = mock_response

        result = call_gemma("Write a story.")

        assert result == "Gemma story."
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "gemma2:2b"
        assert kwargs["json"]["messages"][0]["content"] == "Write a story."

    @patch("app.models.requests.post")
    def test_raises_when_ollama_unavailable(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("connection refused")

        with pytest.raises(requests.ConnectionError):
            call_gemma("Write a story.")


class TestChatWithModel:
    @patch("app.models.chat_openai")
    def test_routes_to_openai(self, mock_chat_openai):
        messages = [{"role": "user", "content": "Hello"}]
        mock_chat_openai.return_value = "Hi there."

        result = chat_with_model(MODEL_GPT, messages)

        assert result == "Hi there."
        mock_chat_openai.assert_called_once_with(messages, max_tokens=3000, temperature=0.7)

    @patch("app.models.chat_gemma")
    def test_routes_to_gemma(self, mock_chat_gemma):
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Tell me a story."},
        ]
        mock_chat_gemma.return_value = "Once upon a time..."

        result = chat_with_model(MODEL_GEMMA, messages)

        assert result == "Once upon a time..."
        mock_chat_gemma.assert_called_once_with(messages, max_tokens=3000, temperature=0.7)


class TestChatOpenAI:
    @patch("app.models.openai.ChatCompletion.create")
    def test_sends_full_message_history(self, mock_create):
        mock_create.return_value = MagicMock(
            choices=[MagicMock(message={"content": "Story time."})]
        )
        messages = [
            {"role": "system", "content": "Be cozy."},
            {"role": "user", "content": "A story about a cat."},
        ]

        result = chat_openai(messages)

        assert result == "Story time."
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["messages"] == messages


class TestChatGemma:
    @patch("app.models.requests.post")
    def test_sends_full_message_history(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Gemma reply."}}
        mock_post.return_value = mock_response
        messages = [
            {"role": "system", "content": "Be cozy."},
            {"role": "user", "content": "A story about a cat."},
            {"role": "assistant", "content": "Draft story."},
            {"role": "user", "content": "Make it shorter."},
        ]

        result = chat_gemma(messages)

        assert result == "Gemma reply."
        assert mock_post.call_args.kwargs["json"]["messages"] == messages

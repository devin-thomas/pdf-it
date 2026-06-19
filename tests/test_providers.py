import pytest

from pdf_it.config import PROVIDER_CONFIGS, Provider
from pdf_it.providers import ProviderRequestError, build_chat_model, safe_provider_error


@pytest.mark.parametrize(
    "provider,module_name,class_name",
    [
        (Provider.GEMINI, "langchain_google_genai", "ChatGoogleGenerativeAI"),
        (Provider.OPENAI, "langchain_openai", "ChatOpenAI"),
        (Provider.ANTHROPIC, "langchain_anthropic", "ChatAnthropic"),
    ],
)
def test_routes_key_to_selected_provider(
    monkeypatch: pytest.MonkeyPatch,
    provider: Provider,
    module_name: str,
    class_name: str,
) -> None:
    captured: dict[str, object] = {}

    def fake_client(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return captured

    module = __import__(module_name)
    monkeypatch.setattr(module, class_name, fake_client)
    result = build_chat_model(provider, "unit-test-key")

    assert result["api_key"] == "unit-test-key"
    assert result["model"] == PROVIDER_CONFIGS[provider].model


def test_missing_key_and_safe_errors_do_not_reflect_provider_details() -> None:
    with pytest.raises(ProviderRequestError, match="Enter an API key"):
        build_chat_model(Provider.GEMINI, "  ")

    original = RuntimeError("401 rejected credential unit-test-sensitive-value")
    safe = safe_provider_error(original)
    assert "unit-test-sensitive-value" not in str(safe)
    assert "rejected" in str(safe)

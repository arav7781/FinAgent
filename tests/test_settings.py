"""Configuration defaults and derived flags."""

from dataclasses import replace

from finagent.settings import Settings, settings


def test_defaults_are_sane():
    assert settings.port == 7860
    assert settings.embedding_dim == 384
    assert settings.chunk_overlap < settings.chunk_size
    assert settings.max_query_rewrites >= 1


def test_optional_integrations_default_to_off():
    blank = Settings(qdrant_url="", mca_api_key="", rapidapi_key="")
    assert blank.qdrant_enabled is False
    assert blank.mca_live is False
    assert blank.market_data_enabled is False


def test_flags_flip_when_configured():
    configured = replace(
        settings,
        qdrant_url="http://localhost:6333",
        mca_api_key="k",
        rapidapi_key="k",
    )
    assert configured.qdrant_enabled
    assert configured.mca_live
    assert configured.market_data_enabled


def test_settings_are_immutable():
    """Settings is frozen, so nothing can mutate configuration at runtime."""
    from dataclasses import FrozenInstanceError

    import pytest

    with pytest.raises(FrozenInstanceError):
        settings.port = 9000  # type: ignore[misc]

from ironman.config import Settings


def test_settings_defaults_are_single_user_and_local_first() -> None:
    settings = Settings()
    assert settings.environment == "development"
    assert settings.auth_mode == "development"
    assert settings.single_user_id == "owner"
    assert settings.database_url.startswith("sqlite:///")

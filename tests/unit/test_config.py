from app.config.settings import Settings


def test_settings_loads_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("ARC_GIS_ENDPOINT", "https://example.com/FeatureServer/0")
    s = Settings()
    assert s.database_url is not None
    assert s.arcgis_endpoint is not None

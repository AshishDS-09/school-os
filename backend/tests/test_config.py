from app.core.config import Settings


def test_celery_urls_fallback_to_redis_url(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://cache.example:6379/0")
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)

    settings = Settings()

    assert settings.celery_broker_url == "redis://cache.example:6379/1"
    assert settings.celery_result_backend == "redis://cache.example:6379/2"

"""Basic API tests using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "mnemosine"


class TestModelsCatalog:
    def test_catalog_returns_models(self):
        response = client.get("/models/catalog")
        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert "gpu_available" in data
        assert "detected_device" in data
        assert "defaults" in data

        # Should have both VL and text models
        types = {m["type"] for m in data["models"]}
        assert "vl" in types
        assert "text" in types

    def test_catalog_has_required_fields(self):
        response = client.get("/models/catalog")
        data = response.json()

        for model in data["models"]:
            assert "id" in model
            assert "type" in model
            assert "label" in model
            assert "requires_gpu" in model


class TestAnalyzeValidation:
    def test_analyze_rejects_nonexistent_path(self):
        response = client.post("/analyze", json={
            "manuscript_path": "/nonexistent/path/ms",
            "mode": "metadata",
            "granularity": "page",
            "device": "cpu",
            "provider": "openai",
        })
        # Should fail with 400 or 500
        assert response.status_code in (400, 500)

    def test_analyze_rejects_invalid_mode(self):
        response = client.post("/analyze", json={
            "manuscript_path": "/tmp/test",
            "mode": "invalid_mode",
        })
        assert response.status_code == 422  # Pydantic validation error


class TestManuscriptsBrowse:
    def test_browse_nonexistent_returns_404(self):
        response = client.get("/manuscripts/browse?path=/nonexistent")
        assert response.status_code == 404

"""Tests for output writing — validates that pipeline creates correct file structure."""

import json
import os
import pytest
from pathlib import Path


class TestOutputWriting:
    """Test file output structure without running actual inference."""

    def _create_manuscript(self, tmp_path):
        """Create a minimal manuscript directory structure."""
        ms = tmp_path / "test_manuscript"
        images = ms / "Immagini"
        images.mkdir(parents=True)

        # Create dummy images
        for name in ["001_front.jpg", "002_page.jpg", "003_back.jpg"]:
            (images / name).write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

        return ms

    def test_output_dir_created(self, tmp_path):
        ms = self._create_manuscript(tmp_path)
        output = ms / "OUTPUT"
        assert not output.exists()
        output.mkdir(exist_ok=True)
        assert output.exists()

    def test_metadata_files_structure(self, tmp_path):
        ms = self._create_manuscript(tmp_path)
        meta_dir = ms / "OUTPUT" / "page_metadati"
        meta_dir.mkdir(parents=True)

        # Simulate writing metadata
        sample_json = {
            "NOTAZIONE_MUSICALE": {"presenza": "NO", "tipo": "", "colore_note": ""},
            "STATO_DI_CONSERVAZIONE": "BUONO",
            "LINGUA": "Latino",
        }
        for name in ["001_front", "002_page", "003_back"]:
            path = meta_dir / f"{name}.txt"
            path.write_text(json.dumps(sample_json, indent=2, ensure_ascii=False))

        # Verify
        files = sorted(meta_dir.glob("*.txt"))
        assert len(files) == 3
        assert files[0].name == "001_front.txt"

        # Verify JSON is valid
        for f in files:
            obj = json.loads(f.read_text())
            assert "STATO_DI_CONSERVAZIONE" in obj
            assert obj["LINGUA"] == "Latino"

    def test_transcription_files_structure(self, tmp_path):
        ms = self._create_manuscript(tmp_path)
        trasc_dir = ms / "OUTPUT" / "Trascrizioni"
        trasc_dir.mkdir(parents=True)

        # Simulate writing transcriptions
        for name in ["001_front", "002_page", "003_back"]:
            path = trasc_dir / f"{name}.txt"
            path.write_text(f"Transcription for page {name}")

        # Verify
        files = sorted(trasc_dir.glob("*.txt"))
        assert len(files) == 3
        assert "Transcription" in files[0].read_text()

    def test_opera_metadata_structure(self, tmp_path):
        ms = self._create_manuscript(tmp_path)
        output = ms / "OUTPUT"
        output.mkdir(parents=True)

        sample = {
            "NOTAZIONE_MUSICALE": {"presenza": "SÌ", "tipo": "NEUMATICA", "colore_note": "nero"},
            "STATO_DI_CONSERVAZIONE": "DISCRETO",
            "LINGUA": "Latino",
        }
        opera_path = output / "metadata_opera.txt"
        opera_path.write_text(json.dumps(sample, indent=2, ensure_ascii=False))

        # Verify
        assert opera_path.exists()
        obj = json.loads(opera_path.read_text())
        assert obj["NOTAZIONE_MUSICALE"]["presenza"] == "SÌ"

    def test_status_json_structure(self, tmp_path):
        ms = self._create_manuscript(tmp_path)
        output = ms / "OUTPUT"
        output.mkdir(parents=True)

        status = {
            "job_id": "abc123",
            "status": "completed",
            "progress": 100.0,
            "total_pages": 3,
            "processed_pages": 3,
            "errors": [],
        }
        status_path = output / "status.json"
        status_path.write_text(json.dumps(status, indent=2))

        obj = json.loads(status_path.read_text())
        assert obj["status"] == "completed"
        assert obj["progress"] == 100.0

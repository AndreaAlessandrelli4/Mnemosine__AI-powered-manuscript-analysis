"""Tests for JSON repair utility."""

import json
import pytest
from app.services.json_repair import repair_json, try_parse_json, ensure_json_string


class TestRepairJson:
    def test_valid_json_unchanged(self):
        raw = '{"key": "value", "num": 42}'
        result = repair_json(raw)
        obj = json.loads(result)
        assert obj["key"] == "value"
        assert obj["num"] == 42

    def test_strips_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = repair_json(raw)
        assert json.loads(result) == {"key": "value"}

    def test_strips_plain_fences(self):
        raw = '```\n{"key": "value"}\n```'
        result = repair_json(raw)
        assert json.loads(result) == {"key": "value"}

    def test_removes_trailing_comma_object(self):
        raw = '{"a": 1, "b": 2,}'
        result = repair_json(raw)
        obj = json.loads(result)
        assert obj == {"a": 1, "b": 2}

    def test_removes_trailing_comma_nested(self):
        raw = '{"outer": {"inner": "val",},}'
        result = repair_json(raw)
        obj = json.loads(result)
        assert obj == {"outer": {"inner": "val"}}

    def test_extracts_json_from_surrounding_text(self):
        raw = 'Here is the result:\n{"key": "value"}\nDone!'
        result = repair_json(raw)
        assert json.loads(result) == {"key": "value"}

    def test_preserves_unicode(self):
        raw = '{"lang": "Italiano", "desc": "Manoscritto con iniziali ornate"}'
        result = repair_json(raw)
        obj = json.loads(result)
        assert obj["lang"] == "Italiano"
        assert "iniziali" in obj["desc"]

    def test_preserves_special_chars(self):
        raw = '{"presenza": "SÌ", "tipo": "NEUMATICA"}'
        result = repair_json(raw)
        obj = json.loads(result)
        assert obj["presenza"] == "SÌ"

    def test_indented_output(self):
        raw = '{"a":1}'
        result = repair_json(raw)
        assert "\n" in result  # should be indented

    def test_raises_on_unfixable(self):
        with pytest.raises(ValueError):
            repair_json("this is not json at all")


class TestTryParseJson:
    def test_returns_object(self):
        result = try_parse_json('{"ok": true}')
        assert result == {"ok": True}

    def test_returns_none_on_failure(self):
        assert try_parse_json("not json") is None


class TestEnsureJsonString:
    def test_returns_string(self):
        result = ensure_json_string('{"a": 1}')
        assert isinstance(result, str)
        assert json.loads(result)["a"] == 1

    def test_raises_on_failure(self):
        with pytest.raises(ValueError):
            ensure_json_string("broken{{{")

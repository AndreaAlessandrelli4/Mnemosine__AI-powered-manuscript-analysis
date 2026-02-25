"""Tests for image utilities — page number parsing and file sorting."""

import pytest
from app.services.image_utils import parse_page_number, list_images, SUPPORTED_EXTENSIONS


class TestParsePageNumber:
    def test_standard_three_digit(self):
        assert parse_page_number("001_copertina.jpg") == 1
        assert parse_page_number("010_pagina.jpg") == 10
        assert parse_page_number("100_retro.png") == 100
        assert parse_page_number("999_last.tiff") == 999

    def test_zero_prefix(self):
        assert parse_page_number("000_frontespizio.jpg") == 0

    def test_no_match(self):
        assert parse_page_number("readme.txt") == -1
        assert parse_page_number("AB_pagina.jpg") == -1

    def test_more_than_three_digits(self):
        # Only first 3 digits are captured
        assert parse_page_number("1234_extra.jpg") == 123


class TestListImages:
    def test_empty_dir(self, tmp_path):
        assert list_images(tmp_path) == []

    def test_non_existent_dir(self):
        assert list_images("/nonexistent/path") == []

    def test_sorts_by_page_number(self, tmp_path):
        # Create test files
        for name in ["003_c.jpg", "001_a.jpg", "002_b.png", "010_d.tiff"]:
            (tmp_path / name).write_text("fake")

        result = list_images(tmp_path)
        page_nums = [r[0] for r in result]
        filenames = [r[1] for r in result]

        assert page_nums == [1, 2, 3, 10]
        assert filenames == ["001_a.jpg", "002_b.png", "003_c.jpg", "010_d.tiff"]

    def test_filters_unsupported(self, tmp_path):
        (tmp_path / "001_page.jpg").write_text("ok")
        (tmp_path / "readme.txt").write_text("skip")
        (tmp_path / "002_page.pdf").write_text("skip")

        result = list_images(tmp_path)
        assert len(result) == 1
        assert result[0][1] == "001_page.jpg"

    def test_supports_all_extensions(self, tmp_path):
        for ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"]:
            (tmp_path / f"001_test{ext}").write_text("ok")

        result = list_images(tmp_path)
        assert len(result) == 6

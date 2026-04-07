"""Tests for parse_exporter_config."""

import pytest
from traitlets.config import Config

from tools.process_wrappers.reporter import parse_exporter_config


class TestParseExporterConfig:
    """Unit tests for the ``parse_exporter_config`` helper."""

    def test_json_boolean_true(self) -> None:
        """JSON ``true`` is decoded as Python ``True``."""
        config = parse_exporter_config(["--WebPDFExporter.exclude_input=true"])
        assert config.WebPDFExporter.exclude_input is True

    def test_json_boolean_false(self) -> None:
        """JSON ``false`` is decoded as Python ``False``."""
        config = parse_exporter_config(["--WebPDFExporter.exclude_input=false"])
        assert config.WebPDFExporter.exclude_input is False

    def test_json_number(self) -> None:
        """Numeric values are decoded as integers."""
        config = parse_exporter_config(["--WebPDFExporter.timeout=120"])
        assert config.WebPDFExporter.timeout == 120

    def test_plain_string_value(self) -> None:
        """Unquoted strings that aren't valid JSON are kept as-is."""
        config = parse_exporter_config(["--HTMLExporter.template_name=classic"])
        assert config.HTMLExporter.template_name == "classic"

    def test_json_quoted_string(self) -> None:
        """JSON-quoted strings are unwrapped."""
        config = parse_exporter_config(['--HTMLExporter.template_name="classic"'])
        assert config.HTMLExporter.template_name == "classic"

    def test_bare_boolean_flag(self) -> None:
        """A flag without ``=value`` is treated as boolean ``True``."""
        config = parse_exporter_config(["--WebPDFExporter.exclude_input"])
        assert config.WebPDFExporter.exclude_input is True

    def test_json_list_value(self) -> None:
        """JSON arrays are decoded as Python lists."""
        config = parse_exporter_config(
            ['--TagRemovePreprocessor.remove_cell_tags=["hide"]']
        )
        assert config.TagRemovePreprocessor.remove_cell_tags == ["hide"]

    def test_multiple_flags(self) -> None:
        """Multiple flags targeting different classes are all applied."""
        config = parse_exporter_config(
            [
                "--WebPDFExporter.exclude_input=true",
                "--HTMLExporter.template_name=classic",
            ]
        )
        assert config.WebPDFExporter.exclude_input is True
        assert config.HTMLExporter.template_name == "classic"

    def test_multiple_traits_same_class(self) -> None:
        """Multiple traits on the same class are all applied."""
        config = parse_exporter_config(
            [
                "--WebPDFExporter.exclude_input=true",
                "--WebPDFExporter.exclude_output=true",
            ]
        )
        assert config.WebPDFExporter.exclude_input is True
        assert config.WebPDFExporter.exclude_output is True

    def test_returns_config_instance(self) -> None:
        """The return value is a ``traitlets.config.Config``."""
        config = parse_exporter_config(["--Foo.bar=1"])
        assert isinstance(config, Config)

    def test_empty_list(self) -> None:
        """An empty flag list returns an empty Config."""
        config = parse_exporter_config([])
        assert isinstance(config, Config)

    def test_missing_trait_name_raises(self) -> None:
        """A flag without a dot-separated trait name raises ValueError."""
        with pytest.raises(ValueError, match="expected --ClassName.trait_name=value"):
            parse_exporter_config(["--WebPDFExporter=true"])

    def test_missing_class_name_raises(self) -> None:
        """A flag without a class name raises ValueError."""
        with pytest.raises(ValueError, match="expected --ClassName.trait_name=value"):
            parse_exporter_config([".trait=true"])

    def test_value_with_equals(self) -> None:
        """Only the first ``=`` splits key from value."""
        config = parse_exporter_config(["--Foo.bar=a=b"])
        assert config.Foo.bar == "a=b"

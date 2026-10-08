"""Tests for parse_exporter_config and the LaTeX exporter configuration."""

import os
from pathlib import Path

import pytest
from traitlets.config import Config

from tools.process_wrappers import reporter
from tools.process_wrappers.reporter import (
    configure_latex,
    latex_exporter_config,
    parse_exporter_config,
)


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


class TestLatexExporterConfig:
    """Unit tests for ``configure_latex`` and ``latex_exporter_config``."""

    @pytest.fixture
    def texmf(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
        """A fake texmf layout with the module level settings reset afterwards."""
        root = tmp_path / "texmf-dist"
        (root / "web2c").mkdir(parents=True)
        cnf = root / "web2c" / "texmf.cnf"
        cnf.write_text("", encoding="utf-8")
        engine = tmp_path / "pdftex"
        engine.write_text("", encoding="utf-8")
        fmt = tmp_path / "formats" / "pdflatex.fmt"
        fmt.parent.mkdir()
        fmt.write_text("", encoding="utf-8")
        for var in ("TEXMF", "TEXMFCNF", "TEXFORMATS", "TEXMFVAR"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setattr(reporter, "_LATEX_SETTINGS", None)
        return {"root": root, "cnf": cnf, "engine": engine, "fmt": fmt, "tmp": tmp_path}

    def test_unconfigured_is_empty(self) -> None:
        """Without ``configure_latex`` nbconvert defaults are left alone."""
        config = latex_exporter_config()
        assert "latex_command" not in config.PDFExporter

    def test_environment(self, texmf: dict[str, Path]) -> None:
        """``TEXMFCNF`` is the cnf directory and ``TEXMF`` its parent."""
        configure_latex(texmf["engine"], texmf["fmt"], texmf["cnf"], None, texmf["tmp"])
        assert Path(os.environ["TEXMFCNF"]) == texmf["root"] / "web2c"
        assert Path(os.environ["TEXMF"]) == texmf["root"]
        assert Path(os.environ["TEXFORMATS"]) == texmf["fmt"].parent
        assert Path(os.environ["TEXMFVAR"]).is_dir()

    def test_latex_command(self, texmf: dict[str, Path]) -> None:
        """The engine is driven through the format and never via PATH lookup."""
        configure_latex(texmf["engine"], texmf["fmt"], texmf["cnf"], None, texmf["tmp"])
        command = latex_exporter_config().PDFExporter.latex_command
        assert command[0] == str(texmf["engine"].absolute())
        assert "-fmt=pdflatex" in command
        assert command[-1] == "{filename}"
        assert "bib_command" not in latex_exporter_config().PDFExporter

    def test_bibtex_command(self, texmf: dict[str, Path]) -> None:
        """A configured bibtex is forwarded to nbconvert."""
        bibtex = texmf["tmp"] / "bibtex8"
        bibtex.write_text("", encoding="utf-8")
        configure_latex(
            texmf["engine"], texmf["fmt"], texmf["cnf"], bibtex, texmf["tmp"]
        )
        command = latex_exporter_config().PDFExporter.bib_command
        assert command == [str(bibtex.absolute()), "{filename}"]

    def test_user_config_overrides(self, texmf: dict[str, Path]) -> None:
        """``--exporter_arg`` values win over the generated defaults."""
        configure_latex(texmf["engine"], texmf["fmt"], texmf["cnf"], None, texmf["tmp"])
        user = parse_exporter_config(["--PDFExporter.latex_count=1"])
        config = latex_exporter_config(user)
        assert config.PDFExporter.latex_count == 1
        assert config.PDFExporter.latex_command[0] == str(texmf["engine"].absolute())

    def test_missing_format_raises(self, texmf: dict[str, Path]) -> None:
        """The format and cnf are mandatory alongside the engine."""
        with pytest.raises(ValueError, match="--latex_format"):
            configure_latex(texmf["engine"], None, texmf["cnf"], None, texmf["tmp"])

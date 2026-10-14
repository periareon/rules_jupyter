"""Tests for the process wrapper runtime."""

import argparse
import json
import os
from pathlib import Path

import pytest
from traitlets.config import Config

from tools.process_wrappers.exporters import (
    REPORT_FORMATS,
    ReportRequest,
    configure_latex,
    latex_exporter_config,
    parse_exporter_config,
    parse_report_templates,
)
from tools.process_wrappers.kernels import (
    DEFAULT_KERNEL_NAME,
    PYTHON_ARGS_TEMPLATE,
    KernelSpec,
    configure_kernelspec,
    parse_kernelspec_rlocations,
)
from tools.process_wrappers.notebook_env import (
    CwdMode,
    add_notebook_arguments,
    inject_args_cell,
    notebook_session,
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
        """A fake texmf layout."""
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
        return {"root": root, "cnf": cnf, "engine": engine, "fmt": fmt, "tmp": tmp_path}

    def test_unconfigured_is_empty(self) -> None:
        """Without a configured toolchain nbconvert defaults are left alone."""
        config = latex_exporter_config(None)
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
        settings = configure_latex(
            texmf["engine"], texmf["fmt"], texmf["cnf"], None, texmf["tmp"]
        )
        command = latex_exporter_config(settings).PDFExporter.latex_command
        assert command[0] == str(texmf["engine"].absolute())
        assert "-fmt=pdflatex" in command
        assert command[-1] == "{filename}"
        assert "bib_command" not in latex_exporter_config(settings).PDFExporter

    def test_bibtex_command(self, texmf: dict[str, Path]) -> None:
        """A configured bibtex is forwarded to nbconvert."""
        bibtex = texmf["tmp"] / "bibtex8"
        bibtex.write_text("", encoding="utf-8")
        settings = configure_latex(
            texmf["engine"], texmf["fmt"], texmf["cnf"], bibtex, texmf["tmp"]
        )
        command = latex_exporter_config(settings).PDFExporter.bib_command
        assert command == [str(bibtex.absolute()), "{filename}"]

    def test_user_config_overrides(self, texmf: dict[str, Path]) -> None:
        """``--exporter_arg`` values win over the generated defaults."""
        settings = configure_latex(
            texmf["engine"], texmf["fmt"], texmf["cnf"], None, texmf["tmp"]
        )
        user = parse_exporter_config(["--PDFExporter.latex_count=1"])
        config = latex_exporter_config(settings, user)
        assert config.PDFExporter.latex_count == 1
        assert config.PDFExporter.latex_command[0] == str(texmf["engine"].absolute())

    def test_missing_format_raises(self, texmf: dict[str, Path]) -> None:
        """The format and cnf are mandatory alongside the engine."""
        with pytest.raises(ValueError, match="--latex_format"):
            configure_latex(texmf["engine"], None, texmf["cnf"], None, texmf["tmp"])


class TestReports:
    """Unit tests for report requests and templates."""

    def test_parse_name_only(self) -> None:
        """A bare name selects the format with no explicit path."""
        request = ReportRequest.parse("html")
        assert request.format is REPORT_FORMATS["html"]
        assert request.path is None

    def test_parse_with_path(self) -> None:
        """``name=path`` carries the output location."""
        request = ReportRequest.parse("pdf=out/report.pdf")
        assert request.format.name == "pdf"
        assert request.path == Path("out/report.pdf")

    def test_parse_unknown_raises(self) -> None:
        """Unknown report names are rejected."""
        with pytest.raises(ValueError, match="Unknown report 'docx'"):
            ReportRequest.parse("docx")

    def test_template_passthrough(self) -> None:
        """Formats without named layouts forward the template name."""
        assert REPORT_FORMATS["html"].template_kwargs("basic") == {
            "template_name": "basic"
        }
        assert not REPORT_FORMATS["html"].template_kwargs(None)

    def test_latex_templates(self) -> None:
        """LaTeX layouts map onto nbconvert template files."""
        kwargs = REPORT_FORMATS["latex"].template_kwargs("report")
        assert kwargs == {"template_name": "latex", "template_file": "report.tex.j2"}
        with pytest.raises(ValueError, match="Unknown latex template type"):
            REPORT_FORMATS["latex"].template_kwargs("book")

    def test_parse_templates(self) -> None:
        """``--report_template`` values are keyed by report."""
        assert parse_report_templates(["html=basic", "latex=report"]) == {
            "html": "basic",
            "latex": "report",
        }
        with pytest.raises(ValueError, match="Invalid --report_template"):
            parse_report_templates(["html"])


class TestKernelSpec:
    """Unit tests for kernelspec loading and installation."""

    @staticmethod
    def _spec(tmp_path: Path, **overrides: object) -> KernelSpec:
        template = tmp_path / "args_template.txt"
        template.write_text("args = {args}", encoding="utf-8")
        data: dict[str, object] = {
            "name": "demo",
            "display_name": "Demo",
            "language": "demo",
            "argv": ["_main/kernel/bin", "--conn", "{connection_file}"],
            "env": {"DEMO_HOME": "_main/kernel/home/${USER}"},
            "args_template": "_main/kernel/args_template.txt",
            "path_tools": ["_main/tools/cargo"],
            "rlocations": [
                "_main/kernel/args_template.txt",
                "_main/kernel/bin",
                "_main/kernel/home",
                "_main/tools/cargo",
            ],
            "transport": "tcp",
        }
        data.update(overrides)
        spec_file = tmp_path / "demo.kernelspec.json"
        spec_file.write_text(json.dumps(data), encoding="utf-8")
        return KernelSpec.from_json(
            spec_file, {"_main/kernel/args_template.txt": template}.__getitem__
        )

    def test_from_json(self, tmp_path: Path) -> None:
        """Every field round trips with optional ones defaulting."""
        spec = self._spec(tmp_path)
        assert spec.name == "demo"
        assert spec.transport == "tcp"
        assert spec.interrupt_mode == ""
        assert spec.args_template == "args = {args}"
        assert spec.path_tools == ["_main/tools/cargo"]

    def test_from_json_without_template(self, tmp_path: Path) -> None:
        """Kernels without a template take no args."""
        spec = self._spec(tmp_path, args_template="")
        assert spec.args_template == ""

    def test_python_kernel(self) -> None:
        """The toolchain's own Python environment is an ordinary kernelspec."""
        spec = KernelSpec.python()
        assert spec.name == DEFAULT_KERNEL_NAME
        assert spec.args_template == PYTHON_ARGS_TEMPLATE
        assert not spec.rlocations
        assert "ipykernel_launcher" in spec.argv

    def test_parse_rlocations(self) -> None:
        """``rlocationpath=path`` pairs become a lookup table."""
        assert parse_kernelspec_rlocations(["a/b=/x/y", "c=d=e"]) == {
            "a/b": Path("/x/y"),
            "c": Path("d=e"),
        }
        with pytest.raises(ValueError, match="expected rlocationpath=path"):
            parse_kernelspec_rlocations(["nope"])

    def test_configure_kernelspec(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Rlocationpaths are substituted and the data dir leads JUPYTER_PATH."""
        monkeypatch.setenv("JUPYTER_PATH", "/existing")
        files = {}
        for rloc in (
            "_main/kernel/args_template.txt",
            "_main/kernel/bin",
            "_main/kernel/home",
            "_main/tools/cargo",
        ):
            path = tmp_path / "runfiles" / rloc
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
            files[rloc] = path

        spec = self._spec(tmp_path)
        data_dir = tmp_path / "jupyter"
        kernel_dir = configure_kernelspec(
            spec, data_dir, files.__getitem__, extra_env={"RUNFILES_DIR": "/rf"}
        )

        kernel_json = json.loads((kernel_dir / "kernel.json").read_text("utf-8"))
        # `_main/kernel/bin` is substituted whole even though `_main/kernel`
        # prefixes other entries; the connection file placeholder survives.
        assert kernel_json["argv"] == [
            str(files["_main/kernel/bin"].absolute()),
            "--conn",
            "{connection_file}",
        ]
        assert kernel_json["env"]["DEMO_HOME"] == (
            str(files["_main/kernel/home"].absolute()) + "/${USER}"
        )
        assert kernel_json["env"]["PATH"].split(os.pathsep) == [
            str(files["_main/tools/cargo"].absolute().parent),
            "${PATH}",
        ]
        assert kernel_json["env"]["RUNFILES_DIR"] == "/rf"
        assert "interrupt_mode" not in kernel_json
        assert os.environ["JUPYTER_PATH"].split(os.pathsep) == [
            str(data_dir),
            "/existing",
        ]

    def test_configure_kernelspec_missing_file(self, tmp_path: Path) -> None:
        """A referenced file that does not exist is an error."""
        spec = self._spec(
            tmp_path, rlocations=["_main/missing"], argv=["x"], args_template=""
        )
        with pytest.raises(FileNotFoundError, match="_main/missing"):
            configure_kernelspec(spec, tmp_path, lambda rloc: tmp_path / rloc)


class TestInjectArgsCell:
    """Unit tests for forwarding notebook args."""

    def test_no_template_no_cell(self) -> None:
        """Nothing is injected for kernels without a template."""
        import nbformat  # pylint: disable=import-outside-toplevel

        notebook = nbformat.v4.new_notebook()  # type: ignore[no-untyped-call]
        inject_args_cell(notebook, [], "", "demo")
        assert not notebook.cells

    def test_empty_params_still_injected(self) -> None:
        """The cell normalizes args even when the target has none."""
        import nbformat  # pylint: disable=import-outside-toplevel

        notebook = nbformat.v4.new_notebook()  # type: ignore[no-untyped-call]
        inject_args_cell(notebook, [], "args = {args}", "demo")
        assert notebook.cells[0].source == "args = []"

    def test_template_without_support_raises(self) -> None:
        """Kernels without a template cannot take params."""
        import nbformat  # pylint: disable=import-outside-toplevel

        notebook = nbformat.v4.new_notebook()  # type: ignore[no-untyped-call]
        with pytest.raises(ValueError, match="does not support notebook args"):
            inject_args_cell(notebook, ["--flag"], "", "demo")

    def test_cell_is_prepended(self) -> None:
        """The template's `{args}` becomes a JSON array in a tagged first cell."""
        import nbformat  # pylint: disable=import-outside-toplevel

        notebook = nbformat.v4.new_notebook()  # type: ignore[no-untyped-call]
        notebook.cells.append(nbformat.v4.new_code_cell("print(1)"))  # type: ignore[no-untyped-call]
        inject_args_cell(notebook, ["--a", "b"], "let args = {args};", "demo")
        assert notebook.cells[0].metadata["tags"] == ["injected-argv"]
        assert json.loads(notebook.cells[0].source[len("let args = ") : -1]) == [
            "--a",
            "b",
        ]
        assert "id" not in notebook.cells[0]


class TestNotebookSession:
    """Unit tests for the shared session setup."""

    @staticmethod
    def _args(tmp_path: Path, *extra: str) -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        add_notebook_arguments(parser)
        notebook = tmp_path / "pkg" / "notebook.ipynb"
        notebook.parent.mkdir(parents=True, exist_ok=True)
        notebook.write_text("{}", encoding="utf-8")
        return parser.parse_args(
            ["--notebook", str(notebook), "--cwd_mode", "notebook_root", *extra]
        )

    def test_defaults_to_python_kernel(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without a kernelspec the toolchain's Python kernel is installed."""
        monkeypatch.delenv("JUPYTER_PATH", raising=False)
        monkeypatch.delenv("IPYTHONDIR", raising=False)
        monkeypatch.setenv("RUNFILES_DIR", "/rf")
        args = self._args(tmp_path)
        home = os.environ.get("HOME")

        with notebook_session(args, runfiles=None, tmp_dir=tmp_path) as session:
            assert session.kernel.name == DEFAULT_KERNEL_NAME
            assert session.cwd == args.notebook.parent
            kernel_json = (
                tmp_path / "jupyter" / "kernels" / DEFAULT_KERNEL_NAME / "kernel.json"
            )
            assert json.loads(kernel_json.read_text("utf-8"))["language"] == "python"
            assert os.environ["JUPYTER_PATH"].startswith(str(tmp_path / "jupyter"))
            assert os.environ["HOME"] == str(tmp_path / "home")
            # The Python kernel shares this process' environment, so runfiles
            # variables stay for it.
            assert os.environ["RUNFILES_DIR"] == "/rf"
            assert not session.reports
            assert session.exporter_config is None

        assert os.environ.get("HOME") == home

    def test_external_kernel_in_action(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An external kernel is resolved from flags and runfiles variables are dropped."""
        monkeypatch.setenv("RUNFILES_DIR", "/rf")
        monkeypatch.setenv("RUNFILES_MANIFEST_FILE", "/rf/MANIFEST")
        binary = tmp_path / "bin" / "kernel"
        binary.parent.mkdir()
        binary.write_text("", encoding="utf-8")
        template = tmp_path / "bin" / "args_template"
        template.write_text("args = {args}", encoding="utf-8")
        spec = tmp_path / "demo.json"
        spec.write_text(
            json.dumps(
                {
                    "name": "demo",
                    "display_name": "Demo",
                    "language": "demo",
                    "argv": ["_main/bin/kernel", "{connection_file}"],
                    "args_template": "_main/bin/args_template",
                    "rlocations": ["_main/bin/args_template", "_main/bin/kernel"],
                    "transport": "tcp",
                }
            ),
            encoding="utf-8",
        )
        pandoc = tmp_path / "pandoc" / "pandoc"
        pandoc.parent.mkdir()
        pandoc.write_text("", encoding="utf-8")
        args = self._args(
            tmp_path,
            "--kernel",
            "demo",
            "--kernelspec",
            str(spec),
            f"--kernelspec_rlocation=_main/bin/kernel={binary}",
            f"--kernelspec_rlocation=_main/bin/args_template={template}",
            "--pandoc",
            str(pandoc),
            "--report",
            "html",
            "--report",
            f"markdown={tmp_path / 'r.md'}",
            "--report_template",
            "html=basic",
            "--exporter_arg=--HTMLExporter.exclude_input=true",
            "--",
            "--flag",
        )

        with notebook_session(args, runfiles=None, tmp_dir=tmp_path) as session:
            assert session.kernel.transport == "tcp"
            assert session.kernel.args_template == "args = {args}"
            assert session.kernel_name == "demo"
            assert session.params == ["--flag"]
            assert [r.format.name for r in session.reports] == ["html", "markdown"]
            assert session.reports[1].path == tmp_path / "r.md"
            assert session.report_templates == {"html": "basic"}
            assert session.exporter_config is not None
            assert session.exporter_config.HTMLExporter.exclude_input is True
            assert os.environ["PATH"].split(os.pathsep)[0] == str(pandoc.parent)
            assert "RUNFILES_DIR" not in os.environ
            assert "RUNFILES_MANIFEST_FILE" not in os.environ
            kernel_json = json.loads(
                (tmp_path / "jupyter" / "kernels" / "demo" / "kernel.json").read_text(
                    "utf-8"
                )
            )
            assert kernel_json["argv"][0] == str(binary.absolute())

    def test_cwd_mode_execution_root(self, tmp_path: Path) -> None:
        """``execution_root`` keeps the process working directory."""
        args = self._args(tmp_path)
        args.cwd_mode = CwdMode.EXECUTION_ROOT
        with notebook_session(args, runfiles=None, tmp_dir=tmp_path) as session:
            assert session.cwd == Path.cwd()

"""Report generation: nbconvert exporters driven by the Bazel toolchain.

Every report a rule can produce is described once in :data:`REPORT_FORMATS`.
The `jupyter_report` action names an explicit output file per report while
tests and binaries only name the format and write next to the notebook; both
go through :func:`export_report`.
"""

import base64
import json
import logging
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import nbformat

_PLOTLY_MIME = "application/vnd.plotly.v1+json"


@dataclass(frozen=True)
class LatexSettings:
    """Resolved locations of the LaTeX toolchain."""

    engine: Path
    format: Path
    texmf_cnf: Path
    bibtex: Optional[Path] = None


# nbconvert >= 6 selects LaTeX layouts by template *file* inside the
# ``latex`` template directory, not by a per-layout template name as
# nbconvert 5 did. Map the rule's layout names onto the modern files.
_LATEX_TEMPLATE_TYPES: dict[str, dict[str, str]] = {
    "article": {"template_name": "latex", "template_file": "index.tex.j2"},
    "report": {"template_name": "latex", "template_file": "report.tex.j2"},
}


@dataclass(frozen=True)
class ReportFormat:
    """A report a notebook can be exported to."""

    name: str
    """The name used by the rules (`reports = [...]`, `out_<name>`)."""
    extension: str
    """The file extension used when no output path is given."""
    exporter: str
    """The ``nbconvert`` exporter class name."""
    templates: Optional[dict[str, dict[str, str]]] = None
    """Named layouts mapped to exporter arguments. ``None`` forwards the
    requested name as ``template_name``."""

    def exporter_class(self, latex: Optional[LatexSettings]) -> type:
        """The exporter class, bound to the LaTeX toolchain where relevant."""
        # `nbconvert` must be imported after the environment is configured.
        import nbconvert  # pylint: disable=import-outside-toplevel

        if self.name == "pdf":
            return pdf_exporter_class(latex)
        return getattr(nbconvert, self.exporter)  # type: ignore[no-any-return]

    def template_kwargs(self, template_type: Optional[str]) -> dict[str, str]:
        """Translate a template type into exporter keyword arguments."""
        if not template_type:
            return {}
        if self.templates is None:
            return {"template_name": template_type}
        try:
            return dict(self.templates[template_type])
        except KeyError:
            raise ValueError(
                f"Unknown {self.name} template type {template_type!r}; "
                f"expected one of {sorted(self.templates)}"
            ) from None


REPORT_FORMATS: dict[str, ReportFormat] = {
    fmt.name: fmt
    for fmt in (
        ReportFormat("html", ".html", "HTMLExporter"),
        ReportFormat("latex", ".tex", "LatexExporter", templates=_LATEX_TEMPLATE_TYPES),
        ReportFormat("markdown", ".md", "MarkdownExporter"),
        ReportFormat("pdf", ".tex.pdf", "PDFExporter"),
        ReportFormat("rst", ".rst", "RSTExporter"),
        ReportFormat("webpdf", ".html.pdf", "WebPDFExporter"),
    )
}
"""Every report format, keyed by name. Mirrored by `_REPORTS` in `jupyter.bzl`."""


@dataclass(frozen=True)
class ReportRequest:
    """A report to produce, optionally at an explicit location."""

    format: ReportFormat
    path: Optional[Path] = None

    @classmethod
    def parse(cls, value: str) -> "ReportRequest":
        """Parse a ``--report`` value of the form ``name`` or ``name=path``."""
        name, has_path, path = value.partition("=")
        if name not in REPORT_FORMATS:
            raise ValueError(
                f"Unknown report {name!r}; expected one of {sorted(REPORT_FORMATS)}"
            )
        return cls(REPORT_FORMATS[name], Path(path) if has_path else None)


def parse_report_templates(entries: list[str]) -> dict[str, str]:
    """Parse ``--report_template`` values of the form ``name=template``."""
    templates = {}
    for entry in entries:
        name, sep, template = entry.partition("=")
        if not sep or name not in REPORT_FORMATS:
            raise ValueError(
                f"Invalid --report_template {entry!r}: expected <report>=<template> "
                f"with a report in {sorted(REPORT_FORMATS)}"
            )
        templates[name] = template
    return templates


def parse_exporter_config(flags: list[str]) -> Any:
    """Parse traitlets-style config flags into a :class:`~traitlets.config.Config`.

    Each flag should follow the ``--ClassName.trait_name=value`` convention used
    by ``jupyter nbconvert`` on the command line.  A bare flag without ``=``
    (e.g. ``--WebPDFExporter.exclude_input``) is treated as boolean ``True``.
    Values are decoded as JSON when possible, otherwise kept as strings.

    Args:
        flags: A list of traitlets config strings
            (e.g. ``["--WebPDFExporter.exclude_input=true"]``).

    Returns:
        A :class:`~traitlets.config.Config` object.
    """
    from traitlets.config import Config  # pylint: disable=import-outside-toplevel

    c = Config()
    for flag in flags:
        key, has_value, raw_value = flag.lstrip("-").partition("=")
        class_name, _, trait_name = key.partition(".")
        if not class_name or not trait_name:
            raise ValueError(
                f"Invalid config flag {flag!r}: expected --ClassName.trait_name=value"
            )
        if not has_value:
            value: Any = True
        else:
            try:
                value = json.loads(raw_value)
            except (json.JSONDecodeError, ValueError):
                value = raw_value
        setattr(c[class_name], trait_name, value)
    return c


def configure_latex(  # pylint: disable=too-many-arguments
    engine: Path,
    fmt: Optional[Path],
    texmf_cnf: Optional[Path],
    bibtex: Optional[Path],
    tmp_dir: Path,
) -> LatexSettings:
    """Configure the environment so a Bazel provided TeX engine can run.

    This mirrors the ``fmtutil`` style invocation used by the ``texlive``
    module: ``TEXMFCNF`` points at the directory holding ``texmf.cnf`` and
    ``TEXMF`` at its parent so ``$TEXMF/tex/...`` and ``$TEXMF/fonts/...``
    lookups resolve inside the hermetic texmf tree. Writable kpathsea
    directories are redirected into *tmp_dir* so the engine never touches
    the user's home directory.

    Args:
        engine: The TeX engine executable.
        fmt: The precompiled format file to load with ``-fmt``.
        texmf_cnf: The ``web2c/texmf.cnf`` anchor file.
        bibtex: An optional bibtex executable.
        tmp_dir: A caller-managed temporary directory.

    Returns:
        The resolved settings for :func:`latex_exporter_config`.
    """
    if fmt is None or texmf_cnf is None:
        raise ValueError(
            "--latex_format and --latex_texmf_cnf are required with --latex_engine"
        )
    for path, what in (
        (engine, "LaTeX engine"),
        (fmt, "LaTeX format"),
        (texmf_cnf, "texmf.cnf"),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{what} not found: {path}")
    if bibtex is not None and not bibtex.exists():
        raise FileNotFoundError(f"bibtex not found: {bibtex}")

    # Use absolute (not resolved) paths so symlink farms such as runfiles
    # trees and sandboxes keep providing exactly the declared files.
    texmf_cnf_dir = texmf_cnf.absolute().parent
    texmf_root = texmf_cnf_dir.parent

    os.environ["TEXMFCNF"] = str(texmf_cnf_dir)
    os.environ["TEXMF"] = str(texmf_root)
    os.environ["TEXMFROOT"] = str(texmf_root)
    os.environ["TEXMFDIST"] = str(texmf_root)
    os.environ["TEXFORMATS"] = str(fmt.absolute().parent)

    for var in (
        "TEXMFVAR",
        "TEXMFSYSVAR",
        "TEXMFCONFIG",
        "TEXMFSYSCONFIG",
        "TEXMFHOME",
    ):
        path = tmp_dir / var.lower()
        path.mkdir(parents=True, exist_ok=True)
        os.environ[var] = str(path)

    settings = LatexSettings(
        engine=engine.absolute(),
        format=fmt.absolute(),
        texmf_cnf=texmf_cnf.absolute(),
        bibtex=bibtex.absolute() if bibtex else None,
    )
    logging.debug("Configured LaTeX: %s", settings)
    return settings


def latex_exporter_config(
    settings: Optional[LatexSettings], user_config: Optional[Any] = None
) -> Any:
    """Build the nbconvert config that drives the hermetic TeX engine.

    User supplied exporter args are merged on top so they can still
    override anything set here.

    Args:
        settings: The configured LaTeX toolchain, if any.
        user_config: An optional :class:`~traitlets.config.Config` from
            ``--exporter_arg`` flags.

    Returns:
        A :class:`~traitlets.config.Config` for ``PDFExporter``.
    """
    from traitlets.config import Config  # pylint: disable=import-outside-toplevel

    config = Config()
    if settings is not None:
        stem = settings.format.stem
        config.PDFExporter.latex_command = [
            str(settings.engine),
            f"-fmt={stem}",
            f"-progname={stem}",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "{filename}",
        ]
        if settings.bibtex is not None:
            config.PDFExporter.bib_command = [str(settings.bibtex), "{filename}"]
    if user_config:
        config.merge(user_config)
    return config


def pdf_exporter_class(settings: Optional[LatexSettings]) -> type:
    """Return a ``PDFExporter`` that skips bibtex when none is configured.

    nbconvert unconditionally runs ``bibtex`` after the first LaTeX pass and
    raises if the executable cannot be found, so the hermetic toolchain needs
    the pass to be optional.
    """
    # pylint: disable=import-outside-toplevel
    from nbconvert import PDFExporter

    class HermeticPDFExporter(PDFExporter):  # pylint: disable=too-many-ancestors
        """``PDFExporter`` bound to the Bazel provided TeX toolchain."""

        def run_bib(self, filename: str, raise_on_failure: Any = False) -> bool:
            if settings is not None and settings.bibtex is None:
                return False
            result = super().run_bib(  # type: ignore[no-untyped-call]
                filename, raise_on_failure
            )
            return bool(result)

    return HermeticPDFExporter


@contextmanager
def _plotly_pdf_workaround(
    notebook: nbformat.NotebookNode, exporter_class: type
) -> Generator[None, None, None]:
    """Strip interactive plotly HTML for PDF export so nbconvert uses image/png.

    WebPDFExporter captures the page before plotly.js finishes rendering,
    producing empty chart containers. The static PNG screenshot is reliable.
    """
    pdf_exporters = ("WebPDFExporter", "PDFExporter")
    if not any(base.__name__ in pdf_exporters for base in exporter_class.__mro__):
        yield
        return

    saved: list[tuple[dict[str, Any], str]] = []
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            if _PLOTLY_MIME in data and "text/html" in data:
                saved.append((data, data.pop("text/html")))
    try:
        yield
    finally:
        for data, html in saved:
            data["text/html"] = html


def export_notebook(
    notebook: nbformat.NotebookNode,
    output_path: Path,
    exporter_class: type,
    *,
    exporter_config: Optional[Any] = None,
    **exporter_kwargs: str,
) -> None:
    """Export a notebook to a specific format.

    Args:
        notebook: The executed notebook.
        output_path: Path to write the output.
        exporter_class: The nbconvert exporter class to use.
        exporter_config: Optional :class:`~traitlets.config.Config` object
            forwarded to the exporter constructor.
        **exporter_kwargs: Further exporter constructor arguments such as
            ``template_name`` or ``template_file``.
    """
    kwargs: dict[str, Any] = dict(exporter_kwargs)
    if exporter_config:
        kwargs["config"] = exporter_config

    exporter = exporter_class(**kwargs)

    with _plotly_pdf_workaround(notebook, exporter_class):
        output, _ = exporter.from_notebook_node(notebook)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(output, bytes):
        output_path.write_bytes(output)
    else:
        output_path.write_text(output, encoding="utf-8")


def export_report(  # pylint: disable=too-many-arguments
    notebook: nbformat.NotebookNode,
    request: ReportRequest,
    *,
    default_dir: Path,
    stem: str,
    template_type: Optional[str] = None,
    exporter_config: Optional[Any] = None,
    latex: Optional[LatexSettings] = None,
) -> Path:
    """Write one report.

    Args:
        notebook: The executed notebook.
        request: The report to produce.
        default_dir: Where to write when the request names no path.
        stem: The file stem used alongside *default_dir*.
        template_type: An optional layout for the format.
        exporter_config: Optional user config from ``--exporter_arg``.
        latex: The configured LaTeX toolchain, required for ``pdf``.

    Returns:
        The path written.
    """
    fmt = request.format
    path = request.path or default_dir / f"{stem}{fmt.extension}"
    config = exporter_config
    if fmt.name == "pdf":
        config = latex_exporter_config(latex, exporter_config)
    export_notebook(
        notebook,
        path,
        fmt.exporter_class(latex),
        exporter_config=config,
        **fmt.template_kwargs(template_type),
    )
    logging.debug("Generated %s report: %s", fmt.name, path)
    return path


def save_notebook(notebook: nbformat.NotebookNode, output_path: Path) -> None:
    """Save a notebook to disk.

    Args:
        notebook: The notebook to save.
        output_path: Path to write the notebook.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(notebook, f)  # type: ignore[no-untyped-call]


def _render_plotly_png_playwright(html: str) -> bytes:
    """Render a plotly HTML page to PNG using the toolchain's Playwright Chromium.

    PLAYWRIGHT_BROWSERS_PATH must already be set via configure_playwright().

    Args:
        html: A full HTML page string containing a plotly chart.

    Returns:
        PNG image bytes of the rendered chart.
    """
    # pylint: disable=import-outside-toplevel
    from playwright.sync_api import sync_playwright

    with tempfile.NamedTemporaryFile(
        suffix=".html", mode="w", encoding="utf-8", delete=False
    ) as f:
        f.write(html)
        html_path = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 800})
            page.goto(f"file://{html_path}", wait_until="networkidle")
            png_bytes = page.locator(".plotly-graph-div").screenshot()
            browser.close()
        return png_bytes
    finally:
        os.unlink(html_path)


def _postprocess_plotly_outputs(notebook: nbformat.NotebookNode) -> None:
    """Convert plotly MIME outputs to renderable formats.

    Plotly's default IPython renderer produces ``application/vnd.plotly.v1+json``
    which nbconvert cannot render. This function adds ``text/html`` (interactive,
    with embedded plotly.js) and ``image/png`` (static, via Playwright screenshot)
    representations so that HTML and WebPDF exports display the charts.

    Plotly is imported conditionally -- it is only needed when the notebook
    actually produced plotly outputs. The notebook's own deps are available
    at runtime because the wrapper venv merges notebook and tool deps.
    """
    plotly_outputs: list[dict[str, Any]] = []
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") in ("display_data", "execute_result"):
                if _PLOTLY_MIME in output.get("data", {}):
                    plotly_outputs.append(output)

    if not plotly_outputs:
        return

    # pylint: disable=import-outside-toplevel
    try:
        import plotly.graph_objects as go  # type: ignore[import-not-found]
    except ImportError:
        logging.warning(
            "Notebook cell outputs contain plotly data but plotly is not "
            "importable. Plotly graphs may not appear in reports."
        )
        return

    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not browsers_path:
        raise RuntimeError(
            "Notebook produces plotly graphs but the Playwright toolchain is "
            "not configured. Set `playwright_browsers_dir` on your "
            "`jupyter_toolchain` to enable plotly graph rendering in reports."
        )

    logging.debug(
        "Post-processing %d plotly output(s) via Playwright", len(plotly_outputs)
    )

    for output in plotly_outputs:
        plotly_json = output["data"][_PLOTLY_MIME]
        fig = go.Figure(data=plotly_json.get("data"), layout=plotly_json.get("layout"))

        output["data"]["text/html"] = fig.to_html(
            full_html=False, include_plotlyjs=True
        )

        full_html = fig.to_html(full_html=True, include_plotlyjs=True)
        png_bytes = _render_plotly_png_playwright(full_html)
        output["data"]["image/png"] = base64.b64encode(png_bytes).decode("ascii")


def postprocess_notebook_outputs(notebook: nbformat.NotebookNode) -> None:
    """Post-process cell outputs so non-standard MIME types render in reports.

    Scans executed notebook cells for library-specific MIME types that
    nbconvert cannot render (e.g. plotly's ``application/vnd.plotly.v1+json``)
    and converts them to standard formats (``text/html``, ``image/png``).
    """
    _postprocess_plotly_outputs(notebook)

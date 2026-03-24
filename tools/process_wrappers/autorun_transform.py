# ---------------------------------------------------------------------------
# Tornado OutputTransform that injects autorun.js into JupyterLab pages.
#
# When the Jupyter server starts, _patched_init_httpserver monkey-patches
# ServerApp.init_httpserver to prepend _AutoRunTransform to the tornado
# application's transform pipeline.  On every /lab/* response that
# contains a </body> tag, the transform appends a <script> element with
# the contents of autorun.js (templated in by lab_launcher.py at
# config-generation time).
#
# The injected script uses window.jupyterapp (exposed via
# page_config.json's exposeAppInBrowser option) to call
# commands.execute("notebook:run-all-cells") once the notebook widget
# and kernel are ready.  See autorun.js for the full polling logic.
#
# The CSP relaxation (_relax_csp) adds 'unsafe-inline' to the
# Content-Security-Policy header so the inline <script> is allowed to
# execute.
# ---------------------------------------------------------------------------

import tornado.web
from jupyter_server.serverapp import ServerApp as _SA

_AUTORUN_SCRIPT = b"""<script>{autorun_script}</script>"""


class _AutoRunTransform(tornado.web.OutputTransform):
    """Inject an auto-run ``<script>`` tag into Lab HTML responses."""

    def __init__(self, request):
        super().__init__(request)
        self._should_inject = request.path.startswith("/lab")

    def _relax_csp(self, headers):
        csp = headers.get("Content-Security-Policy", "")
        if csp and "'unsafe-inline'" not in csp:
            headers["Content-Security-Policy"] = csp.replace(
                "default-src 'self'",
                "default-src 'self' 'unsafe-inline'",
            )

    def transform_first_chunk(self, status_code, headers, chunk, finishing):
        if self._should_inject and b"</body>" in chunk:
            self._relax_csp(headers)
            chunk = chunk.replace(b"</body>", _AUTORUN_SCRIPT + b"</body>", 1)
            cl = headers.get("Content-Length")
            if cl:
                headers["Content-Length"] = str(len(chunk))
            self._should_inject = False
        return status_code, headers, chunk

    def transform_chunk(self, chunk, finishing):
        if self._should_inject and b"</body>" in chunk:
            chunk = chunk.replace(b"</body>", _AUTORUN_SCRIPT + b"</body>", 1)
            self._should_inject = False
        return chunk


# Monkey-patch ServerApp.init_httpserver so the transform is registered
# before the server starts accepting requests.
_orig_init_httpserver = _SA.init_httpserver


def _patched_init_httpserver(self):
    if hasattr(self, "web_app") and self.web_app is not None:
        if not hasattr(self.web_app, "transforms") or self.web_app.transforms is None:
            self.web_app.transforms = []
        self.web_app.transforms.insert(0, _AutoRunTransform)
        print("  [rules_jupyter] Auto-run transform installed", flush=True)
    else:
        print(
            "  [rules_jupyter] WARNING: web_app not available for transform", flush=True
        )
    return _orig_init_httpserver(self)


_SA.init_httpserver = _patched_init_httpserver

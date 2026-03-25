// ibazel reload watcher for rules_jupyter's `jupyter_lab` rule.
//
// Injected alongside autorun.js when running under ibazel with the
// ibazel_notify_changes tag.  Long-polls the server's reload endpoint
// (/api/rules_jupyter/wait_for_reload); when the server signals a
// successful rebuild, reverts the notebook from disk (picking up the
// recompiled .ipynb), restarts the kernel for a clean state, and
// re-executes all cells.
//
// Requires `exposeAppInBrowser: true` in page_config.json (set
// automatically when `execute = True`).

(function() {
    var token = new URLSearchParams(window.location.search).get('token') || '';
    var POLL_URL = '/api/rules_jupyter/wait_for_reload?token=' + encodeURIComponent(token);
    var RUN_CMD = 'notebook:run-all-cells';
    var MAX_CONSECUTIVE_ERRORS = 10;
    var errorCount = 0;

    console.log('[rules_jupyter] ibazel: reload watcher starting');

    function waitForReload() {
        fetch(POLL_URL)
            .then(function(response) {
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.json();
            })
            .then(function(data) {
                if (data.action === 'reload') {
                    errorCount = 0;
                    console.log('[rules_jupyter] ibazel: reload signal received');
                    reloadAndRerun();
                } else {
                    waitForReload();
                }
            })
            .catch(function(err) {
                errorCount++;
                if (errorCount > MAX_CONSECUTIVE_ERRORS) {
                    console.error('[rules_jupyter] ibazel: too many poll errors, stopping');
                    return;
                }
                var delay = Math.min(1000 * Math.pow(2, errorCount - 1), 30000);
                console.warn('[rules_jupyter] ibazel: poll error (' + errorCount + '), retry in ' + delay + 'ms:', err);
                setTimeout(waitForReload, delay);
            });
    }

    function reloadAndRerun() {
        var widget = window.jupyterapp && window.jupyterapp.shell.currentWidget;
        if (!widget || !widget.context) {
            console.warn('[rules_jupyter] ibazel: no active notebook widget, retrying in 500ms');
            setTimeout(function() { reloadAndRerun(); }, 500);
            return;
        }

        // 1. Revert notebook from disk (picks up rebuilt .ipynb content).
        widget.context.revert()
            .then(function() {
                console.log('[rules_jupyter] ibazel: notebook reverted from disk');
                // 2. Restart the kernel for a clean execution environment.
                var session = widget.sessionContext && widget.sessionContext.session;
                if (session && session.kernel) {
                    return session.kernel.restart();
                }
            })
            .then(function() {
                // 3. Wait for the kernel to reach idle before executing.
                return waitForKernelIdle(widget);
            })
            .then(function() {
                console.log('[rules_jupyter] ibazel: executing ' + RUN_CMD);
                return window.jupyterapp.commands.execute(RUN_CMD);
            })
            .then(function() {
                // 4. Resume polling for the next rebuild.
                waitForReload();
            })
            .catch(function(err) {
                console.error('[rules_jupyter] ibazel: reload cycle failed:', err);
                waitForReload();
            });
    }

    function waitForKernelIdle(widget) {
        return new Promise(function(resolve) {
            var attempts = 0;
            var poll = setInterval(function() {
                if (++attempts > 300) {
                    console.warn('[rules_jupyter] ibazel: kernel idle wait timed out');
                    clearInterval(poll);
                    resolve();
                    return;
                }
                var session = widget.sessionContext && widget.sessionContext.session;
                if (session && session.kernel && session.kernel.status === 'idle') {
                    clearInterval(poll);
                    resolve();
                }
            }, 100);
        });
    }

    // Wait for the JupyterLab app to be available before starting.
    var initAttempts = 0;
    var initPoll = setInterval(function() {
        if (++initAttempts > 300) {
            console.warn('[rules_jupyter] ibazel: gave up waiting for jupyterapp');
            clearInterval(initPoll);
            return;
        }
        if (window.jupyterapp) {
            clearInterval(initPoll);
            console.log('[rules_jupyter] ibazel: reload watcher active');
            waitForReload();
        }
    }, 100);
})();

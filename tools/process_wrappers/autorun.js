// Auto-run script for rules_jupyter's `jupyter_lab` rule.
//
// Injected into JupyterLab's HTML by autorun_transform.py (a tornado
// OutputTransform).  Relies on `exposeAppInBrowser: true` in
// page_config.json which makes the JupyterLab application instance
// available as `window.jupyterapp`.  Once the app, the notebook command,
// and the kernel are all ready, fires `notebook:run-all-cells` through
// Lab's public CommandRegistry -- no DOM scraping, no synthetic mouse
// events, and no visibility/focus requirements, so it works even when
// the browser tab is in the background.
//
// A token-scoped localStorage key prevents re-execution on tab reopen
// within the same server session.

(function() {
    // Each `bazel run` invocation generates a unique server token.  Use
    // it to scope the "already ran" guard so a new server session always
    // triggers execution, while reopening a tab in the same session does
    // not.
    var token = new URLSearchParams(window.location.search).get('token') || 'default';
    var key = '__runAll_' + token;
    if (localStorage.getItem(key)) return;

    // Purge stale keys from previous server sessions.
    for (var k = localStorage.length - 1; k >= 0; k--) {
        var old = localStorage.key(k);
        if (old && old.startsWith('__runAll_') && old !== key)
            localStorage.removeItem(old);
    }
    localStorage.setItem(key, '1');
    console.log('[rules_jupyter] autorun: loaded');

    var CMD = 'notebook:run-all-cells';
    var retries = 0;

    // Poll at 100 ms until every prerequisite is satisfied.  The
    // conditions must be checked in dependency order -- each gate
    // requires the previous one to be true.
    var poll = setInterval(function() {
        // Safety timeout: give up after 30 s (300 * 100 ms).
        if (++retries > 300) {
            console.warn('[rules_jupyter] autorun: gave up waiting');
            clearInterval(poll);
            return;
        }

        // 1. The app must be exposed on `window` (requires
        //    exposeAppInBrowser in page_config.json).
        if (!window.jupyterapp) return;

        // 2. The notebook plugin must have registered its commands.
        if (!window.jupyterapp.commands.hasCommand(CMD)) return;

        // 3. A notebook widget must be the active shell widget with a
        //    session context (i.e. Lab has opened the notebook file).
        var widget = window.jupyterapp.shell.currentWidget;
        if (!widget || !widget.sessionContext) return;

        // 4. The kernel must be connected.  Without this guard the
        //    command fires but NotebookActions.runAll() silently skips
        //    every cell because `sessionContext.session.kernel` is null.
        var session = widget.sessionContext.session;
        if (!session || !session.kernel) return;

        clearInterval(poll);
        console.log('[rules_jupyter] autorun: executing ' + CMD);
        window.jupyterapp.commands.execute(CMD);
    }, 100);
})();

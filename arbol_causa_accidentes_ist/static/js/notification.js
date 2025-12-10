// static/js/notification.js
(function () {
    function whenBootstrapReady(cb, tries = 0) {
        if (window.bootstrap && typeof bootstrap.Toast === 'function') { cb(); return; }
        if (tries > 50) return; // ~5s
        setTimeout(function () { whenBootstrapReady(cb, tries + 1); }, 100);
    }

    function showToastsIn(area) {
        if (!area) return;
        area.querySelectorAll('.toast').forEach(function (el) {
        try { new bootstrap.Toast(el).show(); } catch (e) {}
        });
    }

    function showAllToasts() {
        showToastsIn(document.getElementById('toast-area'));
    }

    function setupObserver() {
        var area = document.getElementById('toast-area');
        if (!area || window._toastObserver) return;
        var obs = new MutationObserver(function () { showAllToasts(); });
        obs.observe(area, { childList: true, subtree: true });
        window._toastObserver = obs;
    }

    function setupHTMX() {
        if (!window.htmx || window._toastHTMXBound) return;
        window._toastHTMXBound = true;

        document.body.addEventListener('htmx:afterSettle', function (evt) {
        var tgt = evt && evt.detail && evt.detail.target;
        if (!tgt) return;
        if (tgt.id === 'toast-area' || (tgt.querySelector && tgt.querySelector('#toast-area'))) {
            showAllToasts();
        }
        });

        document.body.addEventListener('htmx:afterOnLoad', function () {
        showAllToasts();
        setupObserver();
        });
    }

    function init() {
        showAllToasts();
        setupObserver();
        setupHTMX();
    }

    function start() {
        whenBootstrapReady(function () {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
        });
    }

    start();
})();

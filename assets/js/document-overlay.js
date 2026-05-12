(function () {
    var TARGET_PATHS = ['/scholars.html', '/endnotes.html'];
    var closeDelay = 180;
    var overlay = null;
    var iframe = null;
    var titleNode = null;
    var closeButton = null;
    var isOpen = false;

    function shouldOpenInOverlay(href) {
        try {
            var url = new URL(href, window.location.href);
            if (url.pathname === window.location.pathname && url.search === window.location.search) {
                return false;
            }
            return TARGET_PATHS.some(function (path) {
                return url.pathname === path || url.pathname.endsWith(path);
            });
        } catch (error) {
            return false;
        }
    }

    function buildOverlay() {
        overlay = document.createElement('div');
        overlay.className = 'document-overlay';
        overlay.hidden = true;
        overlay.setAttribute('aria-hidden', 'true');

        var backdrop = document.createElement('div');
        backdrop.className = 'document-overlay__backdrop';

        var panel = document.createElement('section');
        panel.className = 'document-overlay__panel';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-modal', 'true');
        panel.setAttribute('aria-label', 'Document preview');

        var header = document.createElement('div');
        header.className = 'document-overlay__header';

        titleNode = document.createElement('h2');
        titleNode.className = 'document-overlay__title';
        titleNode.textContent = 'Document preview';

        closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'document-overlay__close';
        closeButton.textContent = 'Close';

        var frame = document.createElement('div');
        frame.className = 'document-overlay__frame';

        iframe = document.createElement('iframe');
        iframe.className = 'document-overlay__iframe';
        iframe.title = 'Document preview';
        iframe.loading = 'lazy';

        frame.appendChild(iframe);
        header.appendChild(titleNode);
        header.appendChild(closeButton);
        panel.appendChild(header);
        panel.appendChild(frame);
        overlay.appendChild(backdrop);
        overlay.appendChild(panel);

        backdrop.addEventListener('click', closeOverlay);
        closeButton.addEventListener('click', closeOverlay);

        document.body.appendChild(overlay);
    }

    function openOverlay(url, titleText) {
        if (!overlay) buildOverlay();

        titleNode.textContent = titleText || 'Document preview';
        iframe.src = url;
        overlay.hidden = false;
        overlay.setAttribute('aria-hidden', 'false');
        document.body.classList.add('document-overlay-open');
        window.setTimeout(function () {
            overlay.classList.add('document-overlay--open');
            closeButton.focus();
        }, 0);
        isOpen = true;
    }

    function closeOverlay() {
        if (!overlay || !isOpen) return;
        overlay.classList.remove('document-overlay--open');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('document-overlay-open');
        isOpen = false;
        window.setTimeout(function () {
            if (!overlay.hidden) {
                overlay.hidden = true;
            }
            iframe.src = 'about:blank';
        }, closeDelay);
    }

    document.addEventListener('click', function (event) {
        var link = event.target.closest('a[href]');
        if (!link) return;
        if (link.target === '_blank' || link.hasAttribute('download')) return;

        var href = link.getAttribute('href');
        if (!href || !shouldOpenInOverlay(href)) return;

        event.preventDefault();
        openOverlay(link.href, link.textContent.trim());
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen) {
            closeOverlay();
        }
    });
})();
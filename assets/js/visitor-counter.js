(function () {
    // Personal visitor counter (page views), hidden from users.
    var COUNTER_NAMESPACE = 'medievalvisions-com';
    var COUNTER_KEY = 'site-visits';

    var host = window.location.hostname;
    if (window.location.protocol === 'file:' || host === 'localhost' || host === '127.0.0.1') {
        return;
    }

    var endpoint = 'https://api.countapi.xyz/hit/'
        + encodeURIComponent(COUNTER_NAMESPACE)
        + '/'
        + encodeURIComponent(COUNTER_KEY);

    fetch(endpoint, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-store',
        keepalive: true
    }).catch(function () {
        // Fail silently; tracking must never affect navigation.
    });
})();

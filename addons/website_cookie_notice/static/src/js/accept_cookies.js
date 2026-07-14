/** Cookie notice - hide banner on click */
document.addEventListener('DOMContentLoaded', function () {
    const btn = document.querySelector('.cc-cookies .btn-primary');
    if (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            fetch('/website_cookie_notice/ok', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {}}),
            }).then(function () {
                const banner = document.querySelector('.cc-cookies');
                if (banner) banner.style.display = 'none';
            });
        });
    }
});

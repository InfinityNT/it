(function () {
    'use strict';

    const timeoutMinutes = parseInt(document.body.dataset.sessionTimeout, 10);
    if (!timeoutMinutes || timeoutMinutes <= 0) return;

    const WARNING_BEFORE_MS = 60 * 1000; // 1 minute warning
    const timeoutMs = timeoutMinutes * 60 * 1000;
    let lastActivity = Date.now();
    let warningTimer = null;
    let countdownInterval = null;
    let modalShown = false;

    const modal = document.getElementById('sessionTimeoutModal');
    if (!modal) return;

    const bsModal = new bootstrap.Modal(modal, { backdrop: 'static', keyboard: false });
    const countdownEl = document.getElementById('sessionTimeoutCountdown');
    const continueBtn = document.getElementById('sessionTimeoutContinue');
    const endBtn = document.getElementById('sessionTimeoutEnd');

    function resetIdleTimer() {
        if (modalShown) return;
        lastActivity = Date.now();
        clearTimeout(warningTimer);
        warningTimer = setTimeout(showWarning, timeoutMs - WARNING_BEFORE_MS);
    }

    function showWarning() {
        modalShown = true;
        let remaining = 60;
        countdownEl.textContent = remaining;
        bsModal.show();

        countdownInterval = setInterval(function () {
            remaining--;
            countdownEl.textContent = remaining;
            if (remaining <= 0) {
                clearInterval(countdownInterval);
                window.location.href = '/login/';
            }
        }, 1000);
    }

    function hideWarning() {
        clearInterval(countdownInterval);
        bsModal.hide();
        modalShown = false;
    }

    continueBtn.addEventListener('click', function () {
        fetch('/api/session/extend/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
        }).then(function () {
            hideWarning();
            resetIdleTimer();
        }).catch(function () {
            window.location.href = '/login/';
        });
    });

    endBtn.addEventListener('click', function () {
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/logout/';
        var csrf = document.createElement('input');
        csrf.type = 'hidden';
        csrf.name = 'csrfmiddlewaretoken';
        csrf.value = getCsrfToken();
        form.appendChild(csrf);
        document.body.appendChild(form);
        form.submit();
    });

    function getCsrfToken() {
        const cookie = document.cookie.split('; ').find(function (c) {
            return c.startsWith('dmp_csrftoken=');
        });
        return cookie ? cookie.split('=')[1] : '';
    }

    // Throttled activity tracking
    let throttleTimeout = null;
    function onActivity() {
        if (throttleTimeout) return;
        throttleTimeout = setTimeout(function () {
            throttleTimeout = null;
        }, 30000); // throttle to once per 30s
        resetIdleTimer();
    }

    ['mousemove', 'keydown', 'click', 'scroll'].forEach(function (evt) {
        document.addEventListener(evt, onActivity, { passive: true });
    });

    // Start the timer
    resetIdleTimer();
})();

window.HELP_IMPROVE_VIDEOJS = false;

(function () {
    function setupNavbarBurger() {
        var burger = document.querySelector('.navbar-burger');
        var menu = document.getElementById('mainNavbar');

        if (!burger || !menu) {
            return;
        }

        burger.addEventListener('click', function () {
            burger.classList.toggle('is-active');
            menu.classList.toggle('is-active');
            burger.setAttribute('aria-expanded', burger.classList.contains('is-active') ? 'true' : 'false');
        });
    }

    function setupCountUp() {
        var counters = document.querySelectorAll('[data-countup]');
        if (!counters.length) {
            return;
        }

        var started = false;

        function animateCounter(el, target) {
            var duration = 1100;
            var startTime = null;

            function step(timestamp) {
                if (!startTime) {
                    startTime = timestamp;
                }
                var progress = Math.min((timestamp - startTime) / duration, 1);
                var value = (target * progress).toFixed(4);
                el.textContent = value;

                if (progress < 1) {
                    requestAnimationFrame(step);
                }
            }

            requestAnimationFrame(step);
        }

        function startWhenVisible(entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting && !started) {
                    started = true;
                    counters.forEach(function (counter) {
                        var target = parseFloat(counter.getAttribute('data-countup'));
                        animateCounter(counter, target);
                    });
                    observer.disconnect();
                }
            });
        }

        var observer = new IntersectionObserver(startWhenVisible, { threshold: 0.35 });
        observer.observe(counters[0]);
    }

    function setupRevealOnScroll() {
        var revealEls = document.querySelectorAll('.reveal-on-scroll');
        if (!revealEls.length) {
            return;
        }

        var observer = new IntersectionObserver(function (entries, obs) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.14 });

        revealEls.forEach(function (el) {
            observer.observe(el);
        });
    }

    function setupTableSearch() {
        var searchInput = document.getElementById('modelSearch');
        var clearBtn = document.getElementById('clearSearch');
        var table = document.getElementById('performanceTable');

        if (!searchInput || !clearBtn || !table) {
            return;
        }

        var rows = table.querySelectorAll('tbody tr');

        function runFilter() {
            var query = searchInput.value.trim().toLowerCase();

            rows.forEach(function (row) {
                var rowText = row.textContent.toLowerCase();
                row.style.display = rowText.indexOf(query) !== -1 ? '' : 'none';
            });
        }

        searchInput.addEventListener('input', runFilter);
        clearBtn.addEventListener('click', function () {
            searchInput.value = '';
            runFilter();
            searchInput.focus();
        });
    }

    function setupBackToTop() {
        var btn = document.getElementById('backToTop');
        if (!btn) {
            return;
        }

        function toggleVisibility() {
            if (window.scrollY > 420) {
                btn.classList.add('visible');
            } else {
                btn.classList.remove('visible');
            }
        }

        window.addEventListener('scroll', toggleVisibility, { passive: true });
        btn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        toggleVisibility();
    }

    function setupImageModal() {
        var modal = document.getElementById('imageModal');
        var modalImage = document.getElementById('modalImage');
        var closeBtn = document.getElementById('closeImageModal');
        var zoomables = document.querySelectorAll('.zoomable-image');

        if (!modal || !modalImage || !closeBtn || !zoomables.length) {
            return;
        }

        function closeModal() {
            modal.classList.remove('open');
            modal.setAttribute('aria-hidden', 'true');
            modalImage.src = '';
        }

        zoomables.forEach(function (img) {
            img.addEventListener('click', function () {
                modalImage.src = img.src;
                modalImage.alt = img.alt || 'Expanded figure';
                modal.classList.add('open');
                modal.setAttribute('aria-hidden', 'false');
            });
        });

        closeBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', function (event) {
            if (event.target === modal) {
                closeModal();
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && modal.classList.contains('open')) {
                closeModal();
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        setupNavbarBurger();
        setupCountUp();
        setupRevealOnScroll();
        setupTableSearch();
        setupBackToTop();
        setupImageModal();
    });
})();

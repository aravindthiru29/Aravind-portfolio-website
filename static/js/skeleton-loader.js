/**
 * skeleton-loader.js — High-performance skeleton loading & progressive image reveal
 * Zero dependencies, CLS-safe, respects prefers-reduced-motion
 */
(function () {
    'use strict';

    function initImageSkeleton(wrap) {
        if (!wrap || wrap.dataset.skeletonInit === 'true') return;
        wrap.dataset.skeletonInit = 'true';

        const img = wrap.querySelector('img');
        if (!img) return;

        // Cache hit or instant load: reveal immediately to avoid shimmer flash
        if (img.complete && img.naturalWidth > 0) {
            wrap.classList.add('is-loaded');
            return;
        }

        const handleLoad = () => {
            wrap.classList.add('is-loaded');
            img.removeEventListener('load', handleLoad);
            img.removeEventListener('error', handleError);
        };

        const handleError = () => {
            wrap.classList.add('is-loaded', 'is-error');
            img.removeEventListener('load', handleLoad);
            img.removeEventListener('error', handleError);
        };

        img.addEventListener('load', handleLoad, { once: true });
        img.addEventListener('error', handleError, { once: true });
    }

    function initAllSkeletons(root = document) {
        const wraps = root.querySelectorAll('.skeleton-img-wrap');
        wraps.forEach(initImageSkeleton);
    }

    // Run as early as possible
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => initAllSkeletons());
    } else {
        initAllSkeletons();
    }

    // Dynamic content observer
    if ('MutationObserver' in window) {
        const observer = new MutationObserver(mutations => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1) {
                        if (node.classList && node.classList.contains('skeleton-img-wrap')) {
                            initImageSkeleton(node);
                        }
                        if (node.querySelectorAll) {
                            initAllSkeletons(node);
                        }
                    }
                }
            }
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }

    // Public API
    window.SkeletonLoader = {
        init: initAllSkeletons,
        initWrap: initImageSkeleton,
        reveal: function (el) {
            if (el) el.classList.add('is-loaded');
        }
    };
})();

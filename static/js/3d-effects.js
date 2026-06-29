/**
 * ============================================================
 * 3D Effects Suite — Aravind Portfolio (v3)
 * ============================================================
 *  • Particle + wireframe background on hero / header sections
 *  • Mouse-reactive camera parallax (global)
 *  • 3D perspective tilt on cards and sidebar
 *  • Scroll-triggered depth-shift on sections
 *  • Floating orb cursor follower
 *  • All effects are theme-aware (light ↔ dark)
 * ============================================================
 */
(function () {
    'use strict';

    /* ─── Theme helpers ─────────────────────────────────────── */
    const isDark = () =>
        document.documentElement.getAttribute('data-theme') === 'dark';

    const palette = () => isDark()
        ? { accent: '#e61c23', soft: '#2a2a2a', bg: '#0b0b0b', glow: 'rgba(230,28,35,0.25)' }
        : { accent: '#d41920', soft: '#cccccc', bg: '#f5f5f5', glow: 'rgba(212,25,32,0.15)' };

    /* ─── Watch theme changes ──────────────────────────────── */
    const themeObserver = new MutationObserver(ev => {
        document.dispatchEvent(new CustomEvent('themechange', { detail: palette() }));
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });


    /* ══════════════════════════════════════════════════════════
       1.  THREE.JS HERO BACKGROUND
       ══════════════════════════════════════════════════════════ */
    function initHeroBackground() {
        const section = document.querySelector('.v2-hero')
            || document.querySelector('.project-hero')
            || document.querySelector('section.v2-section.pt-200');
        if (!section || section.querySelector('#hero-3d-canvas')) return;

        const canvas = document.createElement('canvas');
        canvas.id = 'hero-3d-canvas';
        section.prepend(canvas);

        let W = section.clientWidth;
        let H = Math.max(section.clientHeight, window.innerHeight);

        const scene  = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, W / H, 0.1, 500);
        camera.position.z = 13;

        const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
        renderer.setSize(W, H);

        /* ── Glow texture factory ────────────────────────── */
        function makeGlowTex(r, g, b, size) {
            const c = document.createElement('canvas');
            c.width = c.height = size;
            const ctx = c.getContext('2d');
            const cx = size / 2;
            const gr = ctx.createRadialGradient(cx, cx, 0, cx, cx, cx);
            gr.addColorStop(0,   `rgba(${r},${g},${b},1)`);
            gr.addColorStop(0.25,`rgba(${r},${g},${b},0.8)`);
            gr.addColorStop(0.6, `rgba(${r},${g},${b},0.2)`);
            gr.addColorStop(1,   `rgba(${r},${g},${b},0)`);
            ctx.fillStyle = gr;
            ctx.fillRect(0, 0, size, size);
            return new THREE.CanvasTexture(c);
        }

        /* ── Background particle field ───────────────────── */
        const N   = 900;
        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(N * 3);
        const col = new Float32Array(N * 3);
        const vel = new Float32Array(N * 3);

        function buildParticleColors(p) {
            const a = new THREE.Color(p.accent);
            const s = new THREE.Color(p.soft);
            for (let i = 0; i < N; i++) {
                const c = Math.random() > 0.25 ? s : a;
                col[i*3] = c.r; col[i*3+1] = c.g; col[i*3+2] = c.b;
            }
        }

        for (let i = 0; i < N; i++) {
            pos[i*3]   = (Math.random() - 0.5) * 26;
            pos[i*3+1] = (Math.random() - 0.5) * 26;
            pos[i*3+2] = (Math.random() - 0.5) * 14;
            vel[i*3]   = (Math.random() - 0.5) * 0.003;
            vel[i*3+1] = (Math.random() - 0.5) * 0.003;
        }
        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        geo.setAttribute('color',    new THREE.BufferAttribute(col, 3));
        buildParticleColors(palette());

        const spriteTex = makeGlowTex(255, 255, 255, 64);
        const ptMat = new THREE.PointsMaterial({
            size: 0.10, vertexColors: true, transparent: true,
            opacity: 0.65, depthWrite: false,
            blending: THREE.AdditiveBlending, map: spriteTex
        });
        const points = new THREE.Points(geo, ptMat);
        scene.add(points);

        /* ══════════════════════════════════════════════════
           AI DATA CORE (Replaces Neural Network)
           Nested wireframe shapes and orbiting data nodes.
        ══════════════════════════════════════════════════ */
        const p = palette();
        const aiGroup = new THREE.Group();

        // 1. Central Core Sphere
        const coreGeo = new THREE.IcosahedronGeometry(1.2, 2);
        const coreMat = new THREE.MeshBasicMaterial({
            color: p.accent, wireframe: true, transparent: true,
            opacity: isDark() ? 0.3 : 0.6
        });
        const coreMesh = new THREE.Mesh(coreGeo, coreMat);
        aiGroup.add(coreMesh);

        // 2. Outer Ring / Shell
        const shellGeo = new THREE.IcosahedronGeometry(2.0, 1);
        const shellMat = new THREE.MeshBasicMaterial({
            color: p.soft, wireframe: true, transparent: true,
            opacity: isDark() ? 0.15 : 0.4
        });
        const shellMesh = new THREE.Mesh(shellGeo, shellMat);
        aiGroup.add(shellMesh);

        // 3. Orbiting Data Nodes (Solid)
        const nodeGeo = new THREE.SphereGeometry(0.12, 16, 16);
        const nodeMat = new THREE.MeshBasicMaterial({
            color: p.accent, transparent: true,
            opacity: isDark() ? 0.9 : 1.0
        });
        const nodes = [];
        for (let i = 0; i < 8; i++) {
            const mesh = new THREE.Mesh(nodeGeo, nodeMat);
            // Random orbit parameters
            nodes.push({
                mesh,
                angle: Math.random() * Math.PI * 2,
                speed: 0.01 + Math.random() * 0.015,
                radius: 2.2 + Math.random() * 1.5,
                yOff: (Math.random() - 0.5) * 3
            });
            aiGroup.add(mesh);
        }

        scene.add(aiGroup);

        /* ── Position helper ─────────────────────────────── */
        function positionAI() {
            aiGroup.position.x = W > 992 ? 3.4 : 0;
        }
        positionAI();

        /* ── Mouse parallax ─────────────────────────────── */
        let mx = 0, my = 0, tx = 0, ty = 0;
        document.addEventListener('mousemove', e => {
            mx = (e.clientX - window.innerWidth  / 2) / 140;
            my = (e.clientY - window.innerHeight / 2) / 140;
        });

        /* ── Resize ──────────────────────────────────────── */
        const ro = new ResizeObserver(() => {
            W = section.clientWidth;
            H = Math.max(section.clientHeight, window.innerHeight);
            camera.aspect = W / H;
            camera.updateProjectionMatrix();
            renderer.setSize(W, H);
            positionAI();
        });
        ro.observe(section);

        /* ── Theme reactivity ────────────────────────────── */
        document.addEventListener('themechange', e => {
            const np = e.detail;
            coreMat.color.set(np.accent);
            coreMat.opacity = isDark() ? 0.3 : 0.6;
            shellMat.color.set(np.soft);
            shellMat.opacity = isDark() ? 0.15 : 0.4;
            nodeMat.color.set(np.accent);
            nodeMat.opacity = isDark() ? 0.9 : 1.0;
            buildParticleColors(np);
            geo.attributes.color.needsUpdate = true;
        });

        /* ── Animate ─────────────────────────────────────── */
        let frame = 0;
        (function loop() {
            requestAnimationFrame(loop);
            frame++;
            tx += (mx - tx) * 0.04;
            ty += (my - ty) * 0.04;

            /* AI Data Core sway + mouse parallax */
            aiGroup.rotation.y = tx * 0.06 + frame * 0.002;
            aiGroup.rotation.x = -ty * 0.04 + Math.sin(frame * 0.005) * 0.05;
            aiGroup.position.x = (W > 992 ? 3.4 : 0) + tx * 0.22;
            aiGroup.position.y = -ty * 0.15;

            // Rotate core and shell
            coreMesh.rotation.y -= 0.005;
            coreMesh.rotation.x += 0.003;
            shellMesh.rotation.y += 0.004;
            shellMesh.rotation.z -= 0.002;

            // Orbit nodes
            nodes.forEach(nd => {
                nd.angle += nd.speed;
                nd.mesh.position.x = Math.cos(nd.angle) * nd.radius;
                nd.mesh.position.z = Math.sin(nd.angle) * nd.radius;
                nd.mesh.position.y = nd.yOff + Math.sin(frame * 0.02 + nd.angle) * 0.5;
            });

            /* Drift background particles */
            const posArr = geo.attributes.position.array;
            for (let i = 0; i < N; i++) {
                posArr[i*3]   += vel[i*3];
                posArr[i*3+1] += vel[i*3+1];
                if (posArr[i*3]   >  13) posArr[i*3]   = -13;
                if (posArr[i*3]   < -13) posArr[i*3]   =  13;
                if (posArr[i*3+1] >  13) posArr[i*3+1] = -13;
                if (posArr[i*3+1] < -13) posArr[i*3+1] =  13;
            }
            geo.attributes.position.needsUpdate = true;

            /* Camera parallax on background particles */
            points.rotation.y  =  tx * 0.08;
            points.rotation.x  = -ty * 0.08;

            renderer.render(scene, camera);
        })();
    }

    /* ══════════════════════════════════════════════════════════
       2.  3D TILT ON CARDS & SIDEBAR
       ══════════════════════════════════════════════════════════ */
    function applyTilt(el, maxAngle = 14) {
        if (el.dataset.tilt3d) return;
        el.dataset.tilt3d = '1';
        el.style.transformStyle = 'preserve-3d';
        el.style.willChange     = 'transform';
        el.style.transition     = 'transform 0.6s cubic-bezier(0.25,1,0.5,1), box-shadow 0.6s ease';

        let rafId = null;
        let inside = false;

        const handleMove = (e) => {
            if (rafId) return;  // throttle: only one pending frame at a time
            rafId = requestAnimationFrame(() => {
                rafId = null;
                if (!inside) return;
                const r  = el.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                const x  = clientX - r.left;
                const y  = clientY - r.top;
                const rx = ((r.height / 2 - y) / r.height) * maxAngle;
                const ry = ((x - r.width  / 2) / r.width)  * maxAngle;
                el.style.transition = 'transform 0.08s linear, box-shadow 0.08s linear';
                el.style.transform  = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) scale3d(1.03,1.03,1.03)`;
                el.style.boxShadow  = `${-ry*1.5}px ${rx*1.5}px 30px rgba(0,0,0,0.15), 0 0 16px ${palette().glow}`;
            });
        };

        el.addEventListener('mousemove', handleMove);
        el.addEventListener('touchmove', handleMove, {passive: true});

        el.addEventListener('mouseenter', () => { inside = true; });
        el.addEventListener('touchstart', () => { inside = true; }, {passive: true});

        const reset = () => {
            inside = false;
            if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
            el.style.transition = 'transform 0.6s cubic-bezier(0.25,1,0.5,1), box-shadow 0.6s ease';
            el.style.transform  = 'perspective(900px) rotateX(0deg) rotateY(0deg) scale3d(1,1,1)';
            el.style.boxShadow  = '';
        };

        el.addEventListener('mouseleave', reset);
        el.addEventListener('touchend', reset);
    }

    function initTilt() {
        document.querySelectorAll('.v2-card').forEach(el => applyTilt(el, 12));
        document.querySelectorAll('.detail-sidebar').forEach(el => applyTilt(el, 8));
        document.querySelectorAll('.hover-red-border').forEach(el => applyTilt(el, 10));
        document.querySelectorAll('.v2-hero-img').forEach(el => applyTilt(el, 8));
        document.querySelectorAll('.timeline-item > .row').forEach(el => applyTilt(el, 10));
        document.querySelectorAll('.about-3d-img').forEach(el => applyTilt(el, 14));
    }


    /* ══════════════════════════════════════════════════════════
       3.  FLOATING CURSOR ORB
       ══════════════════════════════════════════════════════════ */
    function initCursorOrb() {
        /* Only on pointer devices */
        if (!window.matchMedia('(pointer:fine)').matches) return;

        const orb = document.createElement('div');
        orb.id = 'cursor-orb';
        orb.style.cssText = `
            position: fixed;
            top: 0; left: 0;
            width: 20px; height: 20px;
            border-radius: 50%;
            background: radial-gradient(circle, ${palette().accent}cc, transparent);
            pointer-events: none;
            z-index: 99999;
            transform: translate(-50%, -50%);
            transition: width 0.2s, height 0.2s, opacity 0.3s;
            mix-blend-mode: screen;
            will-change: transform;
        `;
        document.body.appendChild(orb);

        /* Trailing ring */
        const trail = document.createElement('div');
        trail.id = 'cursor-trail';
        trail.style.cssText = `
            position: fixed;
            top: 0; left: 0;
            width: 40px; height: 40px;
            border-radius: 50%;
            border: 1.5px solid ${palette().accent}88;
            pointer-events: none;
            z-index: 99998;
            transform: translate(-50%, -50%);
            transition: transform 0.12s linear, width 0.2s, height 0.2s, opacity 0.3s;
            will-change: transform;
        `;
        document.body.appendChild(trail);

        let ox = 0, oy = 0, tx2 = 0, ty2 = 0;

        document.addEventListener('mousemove', e => {
            ox = e.clientX;
            oy = e.clientY;
            orb.style.transform   = `translate(${ox - 10}px, ${oy - 10}px)`;
        });

        /* Lazy-follow trail */
        (function orbLoop() {
            requestAnimationFrame(orbLoop);
            tx2 += (ox - tx2) * 0.10;
            ty2 += (oy - ty2) * 0.10;
            trail.style.transform = `translate(${tx2 - 20}px, ${ty2 - 20}px)`;
        })();

        /* Burst on clickable hover */
        document.querySelectorAll('a, button, .v2-card, .v2-btn, .v2-project-item').forEach(el => {
            el.addEventListener('mouseenter', () => {
                orb.style.width   = '36px';
                orb.style.height  = '36px';
                orb.style.opacity = '0.6';
                trail.style.width  = '60px';
                trail.style.height = '60px';
            });
            el.addEventListener('mouseleave', () => {
                orb.style.width   = '20px';
                orb.style.height  = '20px';
                orb.style.opacity = '1';
                trail.style.width  = '40px';
                trail.style.height = '40px';
            });
        });

        /* Update colors on theme change */
        document.addEventListener('themechange', e => {
            orb.style.background   = `radial-gradient(circle, ${e.detail.accent}cc, transparent)`;
            trail.style.borderColor = `${e.detail.accent}88`;
        });
    }


    /* ══════════════════════════════════════════════════════════
       4.  SCROLL PARALLAX DEPTH on sections
       ══════════════════════════════════════════════════════════ */
    function initScrollDepth() {
        const sections = document.querySelectorAll('.v2-section:not(.v2-hero), .project-hero, .v2-section.pt-200');
        if (!sections.length) return;

        let scrollY = window.scrollY;
        let ticking = false;

        const updateDepth = () => {
            sections.forEach(sec => {
                const rect = sec.getBoundingClientRect();
                if (rect.bottom < 0 || rect.top > window.innerHeight) return;
                const progress = (window.innerHeight / 2 - rect.top) / window.innerHeight;
                const shift    = progress * 18; // px shift
                const rotate   = progress * 1.2; // very subtle tilt
                sec.style.transform = `perspective(1200px) rotateX(${-rotate * 0.3}deg) translateZ(0)`;
            });
            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateDepth);
                ticking = true;
            }
        }, { passive: true });
    }


    /* ══════════════════════════════════════════════════════════
       5.  SECTION HEADER 3D TEXT SHADOW on hover
       ══════════════════════════════════════════════════════════ */
    function initTextDepth() {
        document.querySelectorAll('h1, h2').forEach(h => {
            const handleTextMove = (e) => {
                const r = h.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                const x = (clientX - r.left - r.width  / 2) / 18;
                const y = (clientY - r.top  - r.height / 2) / 18;
                h.style.textShadow = `${-x*2}px ${-y*2}px 0 ${palette().accent}55,
                                      ${-x*4}px ${-y*4}px 0 ${palette().accent}30,
                                      ${-x*6}px ${-y*6}px 0 ${palette().accent}15`;
            };
            h.addEventListener('mousemove', handleTextMove);
            h.addEventListener('touchmove', handleTextMove, {passive: true});
            
            const resetText = () => { h.style.textShadow = ''; };
            h.addEventListener('mouseleave', resetText);
            h.addEventListener('touchend', resetText);
        });
    }


    /* ══════════════════════════════════════════════════════════
       BOOT
       ══════════════════════════════════════════════════════════ */
    document.addEventListener('DOMContentLoaded', () => {
        // Defer heavy 3D initialization to allow the browser to paint the LCP (text) first
        setTimeout(() => {
            const isPointer = window.matchMedia('(pointer:fine)').matches;

            /* 3D hero background (Three.js) */
            if (typeof THREE !== 'undefined') {
                initHeroBackground();
            } else {
                console.warn('[3d-effects] Three.js not loaded.');
            }

            if (isPointer) {
                initCursorOrb();
            }
            
            initTilt();
            initTextDepth();

            /* Scroll depth on all devices */
            initScrollDepth();
        }, 150); // Small delay to prioritize text rendering
    });
})();

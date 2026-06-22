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
           GLOWING AI NEURAL NETWORK
           Layers have true Z-depth so it reads as 3D.
           Nodes = camera-facing sprites with soft halo.
           Edges = LineSegments with additive blending.
           16 glowing signal pulses travel along edges.
        ══════════════════════════════════════════════════ */
        const p = palette();
        const nnGroup = new THREE.Group();

        /* Layer definitions: [nodeCount, zDepth] */
        const layerDefs = [
            [3,  2.8],
            [5,  1.4],
            [7,  0.0],
            [5, -1.4],
            [3, -2.8],
        ];
        const LAYER_X_STEP = 1.55;
        const NODE_Y_GAP   = 0.9;

        /* Per-node runtime data */
        const nodeData   = [];   // { pos, coreSpr, haloSpr, coreMat, haloMat }
        const layerNodes = [];   // [[node,...],...]

        /* Textures */
        const nodeCoreTex = makeGlowTex(255, 60, 60, 128);
        const nodeHaloTex = makeGlowTex(230, 28, 35, 256);
        const pulseTex    = makeGlowTex(255, 220, 220, 64);

        layerDefs.forEach(([count, zOff], li) => {
            const x = (li - (layerDefs.length - 1) / 2) * LAYER_X_STEP;
            const layer = [];
            for (let j = 0; j < count; j++) {
                const y = (j - (count - 1) / 2) * NODE_Y_GAP;
                const z = zOff + (Math.random() - 0.5) * 0.35;

                /* Core bright glow */
                const coreMat = new THREE.SpriteMaterial({
                    map: nodeCoreTex, transparent: true, depthWrite: false,
                    blending: THREE.AdditiveBlending,
                    opacity: isDark() ? 0.95 : 0.80
                });
                const core = new THREE.Sprite(coreMat);
                core.scale.set(0.60, 0.60, 1);
                core.position.set(x, y, z);
                nnGroup.add(core);

                /* Outer soft halo */
                const haloMat = new THREE.SpriteMaterial({
                    map: nodeHaloTex, transparent: true, depthWrite: false,
                    blending: THREE.AdditiveBlending,
                    opacity: isDark() ? 0.28 : 0.14
                });
                const halo = new THREE.Sprite(haloMat);
                halo.scale.set(1.6, 1.6, 1);
                halo.position.set(x, y, z);
                nnGroup.add(halo);

                const nd = {
                    pos: new THREE.Vector3(x, y, z),
                    coreSpr: core, haloSpr: halo,
                    coreMat, haloMat,
                    flash: 0   // extra brightness on pulse-arrival
                };
                layer.push(nd);
                nodeData.push(nd);
            }
            layerNodes.push(layer);
        });

        /* Build all inter-layer edge positions into one LineSegments draw call */
        const edgePosArr = [];
        const edgePairs  = [];   // [fromNode, toNode] for pulse routing
        for (let l = 0; l < layerNodes.length - 1; l++) {
            layerNodes[l].forEach(fn => {
                layerNodes[l + 1].forEach(tn => {
                    edgePosArr.push(fn.pos.x, fn.pos.y, fn.pos.z,
                                    tn.pos.x, tn.pos.y, tn.pos.z);
                    edgePairs.push([fn, tn]);
                });
            });
        }
        const edgeGeo = new THREE.BufferGeometry();
        edgeGeo.setAttribute('position',
            new THREE.BufferAttribute(new Float32Array(edgePosArr), 3));
        const edgeMat = new THREE.LineBasicMaterial({
            color: p.accent, transparent: true,
            opacity: isDark() ? 0.18 : 0.10,
            blending: THREE.AdditiveBlending, depthWrite: false
        });
        nnGroup.add(new THREE.LineSegments(edgeGeo, edgeMat));

        /* Glowing signal pulses */
        const pulses = [];
        function spawnPulse() {
            const pIdx = Math.floor(Math.random() * edgePairs.length);
            const [fn, tn] = edgePairs[pIdx];
            const mat = new THREE.SpriteMaterial({
                map: pulseTex, transparent: true, depthWrite: false,
                blending: THREE.AdditiveBlending, opacity: 0.95
            });
            const spr = new THREE.Sprite(mat);
            spr.scale.set(0.32, 0.32, 1);
            nnGroup.add(spr);
            return { spr, mat, from: fn, to: tn, t: 0,
                     speed: 0.007 + Math.random() * 0.009 };
        }
        for (let i = 0; i < 16; i++) {
            const pu = spawnPulse();
            pu.t = Math.random();   // stagger starts
            pulses.push(pu);
        }

        /* Wireframe sphere accent (upper-left background) */
        const accentGeo = new THREE.IcosahedronGeometry(1.4, 2);
        const accentMat = new THREE.MeshBasicMaterial({
            color: p.accent, wireframe: true, transparent: true,
            opacity: isDark() ? 0.13 : 0.07
        });
        const accentSphere = new THREE.Mesh(accentGeo, accentMat);
        accentSphere.position.set(-5.5, 1.5, -2);
        scene.add(accentSphere);

        scene.add(nnGroup);

        /* ── Position helper ─────────────────────────────── */
        function positionNN() {
            nnGroup.position.x = W > 992 ? 3.4 : 0;
        }
        positionNN();

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
            positionNN();
        });
        ro.observe(section);

        /* ── Theme reactivity ────────────────────────────── */
        document.addEventListener('themechange', e => {
            const np = e.detail;
            edgeMat.color.set(np.accent);
            edgeMat.opacity = isDark() ? 0.18 : 0.10;
            accentMat.color.set(np.accent);
            accentMat.opacity = isDark() ? 0.13 : 0.07;
            nodeData.forEach(n => {
                n.coreMat.opacity = isDark() ? 0.95 : 0.80;
                n.haloMat.opacity = isDark() ? 0.28 : 0.14;
            });
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

            /* Neural network sway + mouse parallax */
            nnGroup.rotation.y = tx * 0.06 + Math.sin(frame * 0.008) * 0.10;
            nnGroup.rotation.x = -ty * 0.04 + Math.sin(frame * 0.005) * 0.05;
            nnGroup.position.x = (W > 992 ? 3.4 : 0) + tx * 0.22;
            nnGroup.position.y = -ty * 0.15;

            /* Node breathing: core & halo scale together */
            nodeData.forEach((nd, i) => {
                const breath = 0.75 + Math.sin(frame * 0.042 + i * 0.72) * 0.25;
                // core
                const cs = 0.48 + breath * 0.22;
                nd.coreSpr.scale.set(cs, cs, 1);
                nd.coreMat.opacity = Math.min(1,
                    (isDark() ? 0.70 : 0.55) + breath * (isDark() ? 0.30 : 0.25)
                    + nd.flash * 0.5);
                // halo
                const hs = cs * 2.6;
                nd.haloSpr.scale.set(hs, hs, 1);
                nd.haloMat.opacity = Math.min(0.8,
                    (isDark() ? 0.12 : 0.07) + breath * 0.10
                    + nd.flash * 0.35);
                // decay flash
                nd.flash = Math.max(0, nd.flash - 0.04);
            });

            /* Signal pulses travel along edges */
            pulses.forEach(pu => {
                pu.t += pu.speed;
                if (pu.t >= 1) {
                    /* Flash destination node */
                    pu.to.flash = 1.0;
                    /* Re-assign to a new random edge */
                    const pIdx = Math.floor(Math.random() * edgePairs.length);
                    [pu.from, pu.to] = edgePairs[pIdx];
                    pu.t     = 0;
                    pu.speed = 0.007 + Math.random() * 0.009;
                }
                pu.spr.position.lerpVectors(pu.from.pos, pu.to.pos, pu.t);
                /* Glow brightest at midpoint of travel */
                const glow = Math.sin(pu.t * Math.PI);
                pu.mat.opacity = 0.50 + glow * 0.50;
                const ps = 0.22 + glow * 0.24;
                pu.spr.scale.set(ps, ps, 1);
            });

            /* Wireframe sphere accent spins */
            accentSphere.rotation.y += 0.004;
            accentSphere.rotation.x += 0.002;

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
    function applyTilt(el, maxAngle = 14, depth = 40) {
        if (el.dataset.tilt3d) return;
        el.dataset.tilt3d = '1';
        el.style.transformStyle = 'preserve-3d';
        el.style.willChange     = 'transform';

        /* Elevate direct children for depth illusion */
        el.querySelectorAll('img, h3, h4, .text-red, p, .v2-btn, .detail-label, .detail-value').forEach(child => {
            child.style.transform     = 'translateZ(0)';
            child.style.transition    = 'transform 0.5s cubic-bezier(0.25,1,0.5,1)';
            child.style.willChange    = 'transform';
        });

        el.addEventListener('mousemove', e => {
            const r  = el.getBoundingClientRect();
            const x  = e.clientX - r.left;
            const y  = e.clientY - r.top;
            const rx = ((r.height / 2 - y) / r.height) * maxAngle;
            const ry = ((x - r.width  / 2) / r.width)  * maxAngle;

            el.style.transform  = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) scale3d(1.04,1.04,1.04)`;
            el.style.transition = 'transform 0.06s linear';
            el.style.boxShadow  = `${-ry*2}px ${rx*2}px 40px rgba(0,0,0,0.2), 0 0 20px ${palette().glow}`;

            /* Push children by fraction of depth based on cursor */
            el.querySelectorAll('img').forEach(c => { c.style.transform = `translateZ(${depth}px)`; });
            el.querySelectorAll('h3, h4').forEach(c => { c.style.transform = `translateZ(${depth * 1.2}px)`; });
            el.querySelectorAll('p').forEach(c => { c.style.transform = `translateZ(${depth * 0.8}px)`; });
            el.querySelectorAll('.v2-btn').forEach(c => { c.style.transform = `translateZ(${depth * 1.4}px) scale(1.04)`; });
        });

        el.addEventListener('mouseleave', () => {
            el.style.transform  = 'perspective(900px) rotateX(0deg) rotateY(0deg) scale3d(1,1,1)';
            el.style.transition = 'transform 0.6s cubic-bezier(0.25,1,0.5,1), box-shadow 0.6s ease';
            el.style.boxShadow  = '';
            el.querySelectorAll('img, h3, h4, p, .v2-btn, .text-red, .detail-label, .detail-value').forEach(c => {
                c.style.transform = 'translateZ(0)';
            });
        });
    }

    function initTilt() {
        document.querySelectorAll('.v2-card').forEach(el => applyTilt(el, 15, 45));
        document.querySelectorAll('.detail-sidebar').forEach(el => applyTilt(el, 10, 30));
        document.querySelectorAll('.hover-red-border').forEach(el => applyTilt(el, 12, 25));
        document.querySelectorAll('.v2-hero-img').forEach(el => applyTilt(el, 10, 35));
        document.querySelectorAll('.timeline-item > .row').forEach(el => applyTilt(el, 6, 20));
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
            h.addEventListener('mousemove', e => {
                const r = h.getBoundingClientRect();
                const x = (e.clientX - r.left - r.width  / 2) / 18;
                const y = (e.clientY - r.top  - r.height / 2) / 18;
                h.style.textShadow = `${-x*2}px ${-y*2}px 0 ${palette().accent}55,
                                      ${-x*4}px ${-y*4}px 0 ${palette().accent}30,
                                      ${-x*6}px ${-y*6}px 0 ${palette().accent}15`;
            });
            h.addEventListener('mouseleave', () => { h.style.textShadow = ''; });
        });
    }


    /* ══════════════════════════════════════════════════════════
       BOOT
       ══════════════════════════════════════════════════════════ */
    document.addEventListener('DOMContentLoaded', () => {
        const isPointer = window.matchMedia('(pointer:fine)').matches;

        /* 3D hero background (Three.js) */
        if (typeof THREE !== 'undefined') {
            initHeroBackground();
        } else {
            console.warn('[3d-effects] Three.js not loaded.');
        }

        if (isPointer) {
            initTilt();
            initCursorOrb();
            initTextDepth();
        }

        /* Scroll depth on all devices */
        initScrollDepth();
    });
})();

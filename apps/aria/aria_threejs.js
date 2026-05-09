/**
 * Aria 3D Engine  –  Three.js WebGL character renderer
 *
 * Architecture: CSS State-Mirror
 *   - aria_controller.js keeps running exactly as before (zero changes needed)
 *   - It drives the hidden CSS character (#aria) as its state machine
 *   - This engine reads that state every frame and renders a fully 3D version
 *
 * Game-engine features:
 *   - PBR materials (MeshStandardMaterial) for skin, hair, cloth
 *   - Hemisphere + directional + fill + rim lighting
 *   - PCF soft shadows
 *   - ACES filmic tonemapping
 *   - Procedural anime-style 3D humanoid
 *   - Inverse-kinematics-inspired limb animation
 *   - Mouse-driven 3D eye tracking
 *   - Expression morphing (smile, sad, surprised, etc.)
 *   - Walk cycle, dance, jump, wave, spin animations
 *   - Idle breathing and random blinks
 *   - Background environment (sky gradient, ground plane, particles)
 *   - Post-processing bloom
 */

(function AriaThreeJSEngine() {
    'use strict';

    /* ── Constants ─────────────────────────────────────────────────────── */
    const CHAR_SCALE = 1.22;
    const STAGE_WORLD_W = 8;   // world units (-4 to +4) match CSS 0–100%
    const STAGE_WORLD_H = 5;   // world depth
    const IDLE_BLINK_INTERVAL = 4500; // ms between blink ticks

    /* ── Bootstrap: wait for THREE ──────────────────────────────────────── */
    function bootstrap() {
        if (typeof THREE === 'undefined') { setTimeout(bootstrap, 80); return; }
        const stage = document.getElementById('stage');
        if (!stage) { setTimeout(bootstrap, 80); return; }
        initEngine(stage);
    }
    bootstrap();

    /* ╔══════════════════════════════════════════════════════════════════╗
       ║  ENGINE INIT                                                      ║
       ╚══════════════════════════════════════════════════════════════════╝ */
    function initEngine(stageEl) {
        /* Canvas – inserted as FIRST child so emoji objects overlay it */
        const cv = document.createElement('canvas');
        cv.id = 'ariaCanvas3D';
        cv.style.cssText = [
            'position:absolute', 'inset:0', 'width:100%', 'height:100%',
            'z-index:6', 'border-radius:12px', 'display:block', 'pointer-events:none'
        ].join(';');
        stageEl.insertBefore(cv, stageEl.firstChild);

        /* Renderer */
        const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.05;
        renderer.setClearColor(0x000000, 0); // transparent so CSS bg shows through

        /* Scene */
        const scene = new THREE.Scene();

        /* Camera */
        const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 100);
        camera.position.set(0, 1.72, 5.35);
        camera.lookAt(0, 1.1, 0);

        const clock = new THREE.Clock();

        /* Responsive resize */
        const ro = new ResizeObserver(() => {
            const w = stageEl.offsetWidth, h = stageEl.offsetHeight;
            renderer.setSize(w, h, false);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
        });
        ro.observe(stageEl);
        const w0 = stageEl.offsetWidth, h0 = stageEl.offsetHeight;
        renderer.setSize(w0, h0, false);
        camera.aspect = w0 / h0;
        camera.updateProjectionMatrix();

        /* Build everything */
        const M = buildMaterials();
        buildEnvironment(scene, M, renderer);
        const char = buildCharacter(scene, M);

        /* Mouse tracking */
        const mouse2D = { x: 0, y: 0 };
        cv.addEventListener('mousemove', e => {
            const r = cv.getBoundingClientRect();
            mouse2D.x = ((e.clientX - r.left) / r.width) * 2 - 1;
            mouse2D.y = -((e.clientY - r.top) / r.height) * 2 + 1;
        });
        document.addEventListener('mousemove', e => {
            const r = cv.getBoundingClientRect();
            mouse2D.x = ((e.clientX - r.left) / r.width) * 2 - 1;
            mouse2D.y = -((e.clientY - r.top) / r.height) * 2 + 1;
        });

        /* Anim state */
        const anim = {
            type: 'idle',
            time: 0,
            idleTimer: 0,
            blinkTimer: 0,
            blinkState: 0,
            dancing: false,
            danceTimer: 0,
            walkT: 0,
            jumpT: -1,
            jumpActive: false,
            waveT: -1,
            spinT: -1,
            spinActive: false,
            expression: 'neutral',
            exprBlend: 0,
            charX: 0, charZ: 0,
            targetX: 0, targetZ: 0,
            moodColor: new THREE.Color(0x4a90e2),
            moodIntensity: 0,
        };

        /* ── Render loop ─────────────────────────────────────────────── */
        function loop() {
            requestAnimationFrame(loop);
            const dt = Math.min(clock.getDelta(), 0.06);
            anim.time += dt;

            syncFromCSS(char, anim, stageEl);
            updateCharacter(char, anim, dt, mouse2D, camera);
            renderer.render(scene, camera);
        }
        loop();

        /* Public API for aria_controller.js to call directly if desired */
        window.aria3D = {
            setMood: (color, intensity) => {
                anim.moodColor.set(color || 0x4a90e2);
                anim.moodIntensity = intensity || 0;
            },
            triggerDance: () => { anim.dancing = !anim.dancing; },
            triggerJump: () => { if (anim.jumpT < 0) anim.jumpT = 0; },
            triggerWave: () => { anim.waveT = 0; },
            triggerSpin: () => { anim.spinT = 0; },
            setExpression: (name) => { anim.expression = name; },
            scene, camera, renderer, char
        };
    }

    /* ╔══════════════════════════════════════════════════════════════════╗
       ║  MATERIALS                                                        ║
       ╚══════════════════════════════════════════════════════════════════╝ */
    function buildMaterials() {
        const ph = (params) => new THREE.MeshPhysicalMaterial(params);
        const std = (params) => new THREE.MeshStandardMaterial(params);
        return {
            skin: ph({ color: 0xf5d4b8, roughness: 0.45, metalness: 0.0, clearcoat: 0.2, clearcoatRoughness: 0.35 }),
            skinDeep: ph({ color: 0xe0b898, roughness: 0.47, metalness: 0.0, clearcoat: 0.1, clearcoatRoughness: 0.42 }),
            hair: ph({ color: 0x5e3d2a, roughness: 0.35, metalness: 0.08, clearcoat: 0.65, clearcoatRoughness: 0.5 }),
            hairSheen: ph({ color: 0x8c6248, roughness: 0.25, metalness: 0.18, clearcoat: 0.75, clearcoatRoughness: 0.25 }),
            shirt: ph({ color: 0x4a90e2, roughness: 0.42, metalness: 0.05, clearcoat: 0.1, clearcoatRoughness: 0.4 }),
            skirt: ph({ color: 0xff7eb0, roughness: 0.46, metalness: 0.05, clearcoat: 0.1, clearcoatRoughness: 0.45 }),
            collar: ph({ color: 0xfefefe, roughness: 0.25, metalness: 0.0, clearcoat: 0.4 }),
            bow: ph({ color: 0xff4a8a, roughness: 0.32, metalness: 0.0, clearcoat: 0.25 }),
            pants: ph({ color: 0x3d5a80, roughness: 0.44, metalness: 0.03, clearcoat: 0.08 }),
            shoes: ph({ color: 0xfafafa, roughness: 0.38, metalness: 0.05, clearcoat: 0.18 }),
            soles: ph({ color: 0xdddddd, roughness: 0.69, metalness: 0.0 }),
            eyeWhite: ph({ color: 0xfafcff, roughness: 0.02, metalness: 0.0, clearcoat: 0.25 }),
            eyeIris: ph({ color: 0x3d7fcc, roughness: 0.1, metalness: 0.2, clearcoat: 0.55 }),
            eyeIris2: ph({ color: 0x5a9ee8, roughness: 0.08, metalness: 0.2, clearcoat: 0.55 }),
            eyePupil: ph({ color: 0x0a0808, roughness: 0.04, metalness: 0.4 }),
            eyeShine: ph({ color: 0xffffff, roughness: 0.0, metalness: 0.0, emissive: 0xffffff, emissiveIntensity: 1.2, transparent: true, opacity: 0.9 }),
            eyeLid: ph({ color: 0xf3c8b0, roughness: 0.6, metalness: 0.0 }),
            eyebrow: ph({ color: 0x3c2a1e, roughness: 0.84, metalness: 0.0 }),
            nose: ph({ color: 0xefc0a0, roughness: 0.58, metalness: 0.0 }),
            lips: ph({ color: 0xd9827a, roughness: 0.42, metalness: 0.0, clearcoat: 0.27 }),
            blush: ph({ color: 0xf2a09a, roughness: 0.77, metalness: 0.0, transparent: true, opacity: 0.42 }),
            ground: ph({ color: 0x7cbf8a, roughness: 0.92, metalness: 0.0 }),
            groundLine: ph({ color: 0x679d6e, roughness: 0.92, metalness: 0.0 }),
            table: ph({ color: 0x855633, roughness: 0.74, metalness: 0.01 }),
            tableDark: ph({ color: 0x5c2e08, roughness: 0.9, metalness: 0.0 }),
            particle: std({
                color: 0xffd0e8, roughness: 0.5, metalness: 0,
                transparent: true, opacity: 0.7,
                emissive: 0xffd0e8, emissiveIntensity: 0.4
            }),
        };
    }

    /* ╔══════════════════════════════════════════════════════════════════╗
       ║  ENVIRONMENT                                                      ║
       ╚══════════════════════════════════════════════════════════════════╝ */
    function buildEnvironment(scene, M, renderer) {
        /* Environment gloss: subtle global light bounce */
        const pmrem = new THREE.PMREMGenerator(renderer);
        pmrem.compileEquirectangularShader();
        const envTexture = new THREE.TextureLoader().load('https://cdn.jsdelivr.net/gh/mrdoob/three.js@r152/examples/textures/2294472375_24a3b8ef46_o.jpg', texture => {
            texture.mapping = THREE.EquirectangularReflectionMapping;
            scene.environment = pmrem.fromEquirectangular(texture).texture;
            scene.background = texture;
        });

        /* Hemisphere – sky very soft */
        const hemi = new THREE.HemisphereLight(0xb0d8f5, 0x91d590, 0.65);
        scene.add(hemi);

        /* Main sun – warm, casts shadows */
        const sun = new THREE.DirectionalLight(0xfff6e6, 1.45);
        sun.position.set(4, 10, 6);
        sun.castShadow = true;
        sun.shadow.bias = -0.0008;
        sun.shadow.normalBias = 0.02;
        sun.shadow.camera.near = 1;
        sun.shadow.camera.far = 30;
        sun.shadow.camera.left = sun.shadow.camera.bottom = -6;
        sun.shadow.camera.right = sun.shadow.camera.top = 6;
        sun.shadow.mapSize.set(2048, 2048);
        scene.add(sun);

        /* Cool fill from left */
        const fill = new THREE.DirectionalLight(0xd8eeff, 0.45);
        fill.position.set(-5, 4, 3);
        scene.add(fill);

        /* Rim / backlight – vivid depth */
        const rim = new THREE.PointLight(0xf5e0ff, 0.7, 12);
        rim.position.set(0, 3.5, -4);
        scene.add(rim);

        /* Floor as a soft-lit plane */
        const floor = new THREE.Mesh(new THREE.PlaneGeometry(20, 14), M.ground);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = 0;
        floor.receiveShadow = true;
        scene.add(floor);

        /* Stage table so objects still feel grounded after hiding the CSS one */
        const table = new THREE.Group();
        const tableTop = new THREE.Mesh(
            new THREE.BoxGeometry(1.95, 0.12, 0.92), M.table
        );
        tableTop.castShadow = true;
        tableTop.receiveShadow = true;
        table.add(tableTop);

        const legGeo = new THREE.BoxGeometry(0.10, 0.82, 0.10);
        [
            [-0.82, -0.47, -0.32],
            [0.82, -0.47, -0.32],
            [-0.82, -0.47, 0.32],
            [0.82, -0.47, 0.32],
        ].forEach(([x, y, z]) => {
            const leg = new THREE.Mesh(legGeo, M.tableDark);
            leg.position.set(x, y, z);
            leg.castShadow = true;
            leg.receiveShadow = true;
            table.add(leg);
        });

        table.position.set(1.35, 0.84, -0.55);
        table.rotation.y = -0.18;
        scene.add(table);

        /* Subtle grid lines on floor */
        const grid = new THREE.GridHelper(12, 12, 0x5a9e60, 0x5a9e60);
        grid.position.y = 0.001;
        grid.material.transparent = true;
        grid.material.opacity = 0.12;
        scene.add(grid);

        /* Ambient particles (floating sparkles) */
        const pGeo = new THREE.BufferGeometry();
        const COUNT = 60;
        const pPos = new Float32Array(COUNT * 3);
        for (let i = 0; i < COUNT; i++) {
            pPos[i * 3] = (Math.random() - 0.5) * 7;
            pPos[i * 3 + 1] = Math.random() * 3.5 + 0.3;
            pPos[i * 3 + 2] = (Math.random() - 0.5) * 4 - 1;
        }
        pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
        const pts = new THREE.Points(pGeo, new THREE.PointsMaterial({
            color: 0xfff0f8, size: 0.025, transparent: true, opacity: 0.55
        }));
        pts.userData.isParticle = true;
        pts.userData.basePos = pPos.slice();
        scene.add(pts);

        /* Background gradient fog */
        scene.fog = new THREE.FogExp2(0xd8eef8, 0.045);
    }

    /* ╔══════════════════════════════════════════════════════════════════╗
       ║  CHARACTER CONSTRUCTION                                           ║
       ╚══════════════════════════════════════════════════════════════════╝ */
    function buildCharacter(scene, M) {
        const root = new THREE.Group();
        root.name = 'ariaRoot';

        /* ── Legs (before torso so hip joint is clear) ── */
        const hipGroup = new THREE.Group(); hipGroup.name = 'hips';
        hipGroup.position.set(0, 0.82, 0);

        const legL = buildLeg('L', M);
        legL.position.set(-0.13, 0, 0);
        hipGroup.add(legL);

        const legR = buildLeg('R', M);
        legR.position.set(0.13, 0, 0);
        hipGroup.add(legR);

        root.add(hipGroup);

        /* ── Torso ── */
        const torsoGroup = new THREE.Group(); torsoGroup.name = 'torso';
        torsoGroup.position.set(0, 0.82, 0); // starts at hip height

        /* Pelvis / waist */
        const waist = new THREE.Mesh(
            new THREE.CylinderGeometry(0.155, 0.165, 0.18, 20), M.shirt);
        waist.position.y = 0;
        waist.castShadow = true;
        torsoGroup.add(waist);

        /* Main shirt body */
        const torsoMesh = new THREE.Mesh(
            new THREE.CylinderGeometry(0.182, 0.148, 0.46, 22), M.shirt);
        torsoMesh.position.y = 0.31;
        torsoMesh.castShadow = true;
        torsoGroup.add(torsoMesh);

        /* Chest highlight */
        const chestFront = new THREE.Mesh(
            new THREE.SphereGeometry(0.16, 16, 10), M.shirt);
        chestFront.position.set(0, 0.47, 0.07);
        chestFront.scale.set(0.95, 0.82, 0.52);
        chestFront.castShadow = true;
        torsoGroup.add(chestFront);

        /* ── Dress skirt (lathe) ── */
        const skirtPoints = [];
        const skirtProfile = [
            [0.148, 0], [0.158, -0.05], [0.178, -0.13], [0.205, -0.24],
            [0.245, -0.36], [0.285, -0.48], [0.315, -0.58], [0.325, -0.66]
        ];
        skirtProfile.forEach(([r, y]) => skirtPoints.push(new THREE.Vector2(r, y)));
        const skirtMesh = new THREE.Mesh(
            new THREE.LatheGeometry(skirtPoints, 28), M.skirt);
        skirtMesh.position.y = 0.07;
        skirtMesh.castShadow = true;
        torsoGroup.add(skirtMesh);

        /* Collar / shirt neckline */
        const collarMesh = new THREE.Mesh(
            new THREE.TorusGeometry(0.095, 0.022, 8, 20), M.collar);
        collarMesh.position.y = 0.53;
        collarMesh.rotation.x = 0.2;
        collarMesh.castShadow = true;
        torsoGroup.add(collarMesh);

        /* Bow tie */
        const bowL = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.032, 0.02), M.bow);
        bowL.position.set(-0.03, 0.56, 0.10);
        bowL.rotation.z = 0.35;
        const bowR = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.032, 0.02), M.bow);
        bowR.position.set(0.03, 0.56, 0.10);
        bowR.rotation.z = -0.35;
        const bowCenter = new THREE.Mesh(new THREE.SphereGeometry(0.018, 8, 8), M.bow);
        bowCenter.position.set(0, 0.56, 0.11);
        [bowL, bowR, bowCenter].forEach(b => { b.castShadow = true; torsoGroup.add(b); });

        /* ── Arms ── */
        const shoulderGroupL = new THREE.Group(); shoulderGroupL.name = 'shoulderL';
        shoulderGroupL.position.set(-0.22, 0.50, 0);
        const armL = buildArm('L', M);
        shoulderGroupL.add(armL);
        torsoGroup.add(shoulderGroupL);

        const shoulderGroupR = new THREE.Group(); shoulderGroupR.name = 'shoulderR';
        shoulderGroupR.position.set(0.22, 0.50, 0);
        const armR = buildArm('R', M);
        shoulderGroupR.add(armR);
        torsoGroup.add(shoulderGroupR);

        /* ── Neck ── */
        const neck = new THREE.Mesh(
            new THREE.CylinderGeometry(0.06, 0.072, 0.16, 16), M.skin);
        neck.position.y = 0.62;
        neck.castShadow = true;
        torsoGroup.add(neck);

        /* ── Head ── */
        const headGroup = buildHead(M);
        headGroup.position.y = 0.78;
        torsoGroup.add(headGroup);

        root.add(torsoGroup);

        /* ── Assemble & place ── */
        root.position.set(0, 0, 0);
        root.scale.setScalar(CHAR_SCALE);
        root.rotation.y = 0.22;
        scene.add(root);

        /* Ground shadow disc */
        const shadow = new THREE.Mesh(
            new THREE.CircleGeometry(0.32, 24),
            new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.18 })
        );
        shadow.rotation.x = -Math.PI / 2;
        shadow.position.y = 0.001;
        root.add(shadow);

        return {
            root, torsoGroup, hipGroup, headGroup,
            shoulderGroupL, shoulderGroupR, armL, armR,
            legL, legR, skirtMesh,
            moodLight: (() => {
                const ml = new THREE.PointLight(0x4a90e2, 0, 4);
                ml.position.set(0, 1.5, 0.5);
                root.add(ml);
                return ml;
            })(),
        };
    }

    /* ── Head ──────────────────────────────────────────────────────────── */
    function buildHead(M) {
        const g = new THREE.Group(); g.name = 'head';

        /* Skull */
        const skull = new THREE.Mesh(
            new THREE.SphereGeometry(0.225, 32, 24), M.skin);
        skull.scale.set(1.04, 1.06, 0.9);
        skull.castShadow = true;
        g.add(skull);

        const jaw = new THREE.Mesh(
            new THREE.SphereGeometry(0.155, 20, 14), M.skinDeep);
        jaw.position.set(0, -0.11, 0.01);
        jaw.scale.set(1.02, 0.82, 0.78);
        jaw.castShadow = true;
        g.add(jaw);

        /* Ears */
        [-1, 1].forEach(side => {
            const ear = new THREE.Mesh(
                new THREE.SphereGeometry(0.046, 10, 8), M.skin);
            ear.position.set(side * 0.215, -0.02, 0);
            ear.scale.set(0.55, 0.8, 0.6);
            ear.castShadow = true;
            g.add(ear);
        });

        /* ── Hair ── */
        /* main cap */
        const hairCap = new THREE.Mesh(
            new THREE.SphereGeometry(0.25, 30, 24, 0, Math.PI * 2, 0, Math.PI * 0.66), M.hair);
        hairCap.position.y = 0.035;
        hairCap.scale.set(1.02, 1.05, 0.96);
        hairCap.castShadow = true;
        g.add(hairCap);

        const backHair = new THREE.Mesh(
            new THREE.SphereGeometry(0.205, 20, 18), M.hair);
        backHair.position.set(0, -0.03, -0.09);
        backHair.scale.set(1.02, 1.25, 0.72);
        backHair.castShadow = true;
        g.add(backHair);

        /* Side hair volumes */
        const sideHairGeo = new THREE.SphereGeometry(0.14, 14, 10);
        [-1, 1].forEach(side => {
            const sh = new THREE.Mesh(sideHairGeo, M.hair);
            sh.position.set(side * 0.18, -0.03, -0.03);
            sh.scale.set(0.74, 1.22, 0.78);
            sh.castShadow = true;
            g.add(sh);
        });

        /* Bangs (front hair wisps) */
        const bangData = [
            { x: -0.09, y: 0.12, rz: 0.22, sx: 0.48, sy: 1.35, sz: 0.82 },
            { x: 0.00, y: 0.125, rz: 0.0, sx: 0.56, sy: 1.55, sz: 0.86 },
            { x: 0.09, y: 0.12, rz: -0.22, sx: 0.48, sy: 1.35, sz: 0.82 },
        ];
        bangData.forEach(d => {
            const bang = new THREE.Mesh(new THREE.SphereGeometry(0.09, 10, 8), M.hair);
            bang.position.set(d.x, d.y, 0.15);
            bang.rotation.z = d.rz;
            bang.scale.set(d.sx, d.sy, d.sz);
            bang.castShadow = true;
            g.add(bang);
        });

        /* Ponytails */
        [-1, 1].forEach(side => {
            const pt = new THREE.Group();
            const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8), M.hair);
            s1.scale.set(0.58, 0.92, 0.5);
            const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.06, 10, 8), M.hair);
            s2.position.y = -0.085;
            s2.scale.set(0.46, 1.05, 0.44);
            const s3 = new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 8), M.hair);
            s3.position.y = -0.17;
            s3.scale.set(0.36, 0.95, 0.36);
            pt.add(s1, s2, s3);
            pt.position.set(side * 0.215, -0.03, -0.05);
            pt.rotation.z = side * 0.3;
            pt.rotation.x = 0.08;
            g.add(pt);
        });

        /* ── Eyes ── */
        const eyeData = [
            { x: -0.078, side: 'L' },
            { x: 0.078, side: 'R' },
        ];
        eyeData.forEach(({ x, side }) => {
            const eyeGrp = buildEye(side, M);
            eyeGrp.position.set(x, 0.03, 0.182);
            g.add(eyeGrp);
            g[`eye${side}`] = eyeGrp;
        });

        /* ── Eyebrows ── */
        const brGeo = new THREE.BoxGeometry(0.09, 0.012, 0.018);
        [-1, 1].forEach((side, i) => {
            const br = new THREE.Mesh(brGeo, M.eyebrow);
            br.position.set(side * -0.08, 0.102, 0.18);
            br.rotation.z = side * 0.12;
            br.name = `eyebrow${i === 0 ? 'L' : 'R'}`;
            g.add(br);
            g[`eyebrow${i === 0 ? 'L' : 'R'}`] = br;
        });

        /* ── Nose ── */
        const nose = new THREE.Mesh(
            new THREE.SphereGeometry(0.022, 8, 6), M.nose);
        nose.position.set(0, -0.01, 0.205);
        nose.scale.set(0.95, 0.7, 0.72);
        g.add(nose);

        /* ── Mouth ── */
        const mouthGrp = new THREE.Group(); mouthGrp.name = 'mouth';
        const upperLip = new THREE.Mesh(
            new THREE.TorusGeometry(0.040, 0.010, 6, 14, Math.PI), M.lips);
        upperLip.position.set(0, 0, 0);
        upperLip.rotation.z = Math.PI;
        const lowerLip = new THREE.Mesh(
            new THREE.TorusGeometry(0.038, 0.012, 6, 14, Math.PI), M.lips);
        lowerLip.position.y = -0.009;
        mouthGrp.add(upperLip, lowerLip);
        mouthGrp.position.set(0, -0.095, 0.188);
        mouthGrp.name = 'mouth';
        g.add(mouthGrp);
        g.mouth = mouthGrp;

        /* ── Blush ── */
        [-1, 1].forEach(side => {
            const bl = new THREE.Mesh(
                new THREE.CircleGeometry(0.048, 16), M.blush);
            bl.position.set(side * -0.135, -0.045, 0.16);
            bl.rotation.set(0, side * 0.4, 0);
            g.add(bl);
        });

        return g;
    }

    /* ── Single Eye ─────────────────────────────────────────────────────── */
    function buildEye(side, M) {
        const g = new THREE.Group(); g.name = `eye_${side}`;

        /* Sclera */
        const sclera = new THREE.Mesh(
            new THREE.SphereGeometry(0.051, 18, 14), M.eyeWhite);
        sclera.scale.set(1, 1.04, 0.7);
        sclera.castShadow = false;
        g.add(sclera);

        /* Iris group (tracks mouse) */
        const irisGrp = new THREE.Group(); irisGrp.name = `irisGrp_${side}`;
        const iris = new THREE.Mesh(
            new THREE.SphereGeometry(0.03, 16, 14), M.eyeIris);
        iris.position.z = 0.017;
        iris.scale.set(1, 1.04, 0.7);

        /* Iris gradient ring */
        const irisRing = new THREE.Mesh(
            new THREE.TorusGeometry(0.02, 0.009, 6, 16), M.eyeIris2);
        irisRing.position.z = 0.02;
        irisRing.scale.set(1, 1.02, 0.7);

        /* Pupil */
        const pupil = new THREE.Mesh(
            new THREE.SphereGeometry(0.014, 10, 10), M.eyePupil);
        pupil.position.z = 0.036;

        /* Shine 1 */
        const shine1 = new THREE.Mesh(
            new THREE.SphereGeometry(0.0065, 6, 6), M.eyeShine);
        shine1.position.set(-0.009, 0.012, 0.044);

        /* Shine 2 (small) */
        const shine2 = new THREE.Mesh(
            new THREE.SphereGeometry(0.0035, 6, 6), M.eyeShine);
        shine2.position.set(0.010, -0.008, 0.042);

        irisGrp.add(iris, irisRing, pupil, shine1, shine2);
        g.add(irisGrp);
        g.irisGrp = irisGrp;

        /* Upper eyelid shadow */
        const lidGeo = new THREE.SphereGeometry(0.053, 16, 8, 0, Math.PI * 2, 0, Math.PI * 0.42);
        const lid = new THREE.Mesh(lidGeo, M.eyeLid);
        lid.position.y = 0.008;
        lid.rotation.x = 0.15;
        lid.scale.set(1, 1.0, 0.72);
        g.add(lid);
        g.lid = lid;  // used for blinking

        return g;
    }

    /* ── Arm ──────────────────────────────────────────────────────────────── */
    function buildArm(side, M) {
        const g = new THREE.Group(); g.name = `arm_${side}`;
        g.userData.side = side;

        /* Shoulder ball */
        const sh = new THREE.Mesh(new THREE.SphereGeometry(0.075, 14, 12), M.shirt);
        sh.castShadow = true;
        g.add(sh);

        /* Upper arm */
        const uaGrp = new THREE.Group(); uaGrp.name = `upperArm_${side}`;
        uaGrp.position.y = -0.08;
        const ua = new THREE.Mesh(
            new THREE.CapsuleGeometry(0.052, 0.20, 6, 14), M.skin);
        ua.position.y = -0.10;
        ua.castShadow = true;
        uaGrp.add(ua);

        /* Elbow */
        const elbow = new THREE.Mesh(new THREE.SphereGeometry(0.055, 10, 8), M.skinDeep);
        elbow.position.y = -0.215;
        elbow.castShadow = true;
        uaGrp.add(elbow);

        /* Lower arm */
        const laGrp = new THREE.Group(); laGrp.name = `lowerArm_${side}`;
        laGrp.position.y = -0.215;
        const la = new THREE.Mesh(
            new THREE.CapsuleGeometry(0.045, 0.18, 6, 12), M.skin);
        la.position.y = -0.09;
        la.castShadow = true;
        laGrp.add(la);

        /* Hand */
        const hand = new THREE.Mesh(
            new THREE.SphereGeometry(0.055, 14, 12), M.skin);
        hand.scale.set(1, 0.85, 0.75);
        hand.position.y = -0.195;
        hand.castShadow = true;
        laGrp.add(hand);

        /* Thumb nub */
        const thumb = new THREE.Mesh(new THREE.CapsuleGeometry(0.016, 0.032, 4, 8), M.skin);
        const thumbDir = side === 'L' ? -1 : 1;
        thumb.position.set(thumbDir * 0.05, -0.175, 0.02);
        thumb.rotation.z = thumbDir * 0.9;
        laGrp.add(thumb);

        uaGrp.add(laGrp);
        g.add(uaGrp);
        g.uaGrp = uaGrp;
        g.laGrp = laGrp;

        /* Resting pose: arms slightly down and out */
        uaGrp.rotation.z = side === 'L' ? -0.18 : 0.18;
        return g;
    }

    /* ── Leg ──────────────────────────────────────────────────────────────── */
    function buildLeg(side, M) {
        const g = new THREE.Group(); g.name = `leg_${side}`;

        /* Upper leg (thigh) */
        const ulGrp = new THREE.Group(); ulGrp.name = `upperLeg_${side}`;
        const ul = new THREE.Mesh(
            new THREE.CapsuleGeometry(0.066, 0.26, 8, 16), M.pants);
        ul.position.y = -0.13;
        ul.castShadow = true;
        ulGrp.add(ul);

        /* Knee */
        const knee = new THREE.Mesh(new THREE.SphereGeometry(0.065, 12, 10), M.skinDeep);
        knee.position.y = -0.275;
        knee.castShadow = true;
        ulGrp.add(knee);

        /* Lower leg (calf/shin) */
        const llGrp = new THREE.Group(); llGrp.name = `lowerLeg_${side}`;
        llGrp.position.y = -0.275;
        const ll = new THREE.Mesh(
            new THREE.CapsuleGeometry(0.056, 0.22, 8, 14), M.skin);
        ll.position.y = -0.11;
        ll.castShadow = true;
        llGrp.add(ll);

        /* Ankle */
        const ankle = new THREE.Mesh(new THREE.SphereGeometry(0.050, 10, 8), M.skinDeep);
        ankle.position.y = -0.238;
        llGrp.add(ankle);

        /* Foot / shoe */
        const foot = new THREE.Mesh(
            new THREE.BoxGeometry(0.10, 0.065, 0.22), M.shoes);
        foot.position.set(0, -0.278, 0.045);
        foot.castShadow = true;
        llGrp.add(foot);

        /* Sole */
        const sole = new THREE.Mesh(
            new THREE.BoxGeometry(0.098, 0.018, 0.218), M.soles);
        sole.position.set(0, -0.31, 0.045);
        llGrp.add(sole);

        ulGrp.add(llGrp);
        g.add(ulGrp);
        g.ulGrp = ulGrp;
        g.llGrp = llGrp;

        return g;
    }

    /* ╔══════════════════════════════════════════════════════════════════╗
       ║  CSS STATE SYNC                                                   ║
       ╚══════════════════════════════════════════════════════════════════╝ */
    function syncFromCSS(char, anim, stageEl) {
        const ariaEl = document.getElementById('aria');
        if (!ariaEl) return;

        /* ── Position ── */
        const stW = stageEl.offsetWidth || 600;
        const stH = stageEl.offsetHeight || 500;
        const cs = window.getComputedStyle(ariaEl);
        const leftPx = parseFloat(cs.left) || 0;
        const bottomPx = parseFloat(cs.bottom) || 0;

        // CSS bottom% → world Z (closer/farther), left% → world X
        const xPct = leftPx / stW;  // 0-1
        const yPct = bottomPx / stH;  // 0-1

        anim.targetX = (xPct - 0.5) * STAGE_WORLD_W;
        anim.targetZ = (0.5 - yPct) * STAGE_WORLD_H * 0.5; // y→z depth

        /* ── Animation state from classes ── */
        const cl = ariaEl.classList;
        if (cl.contains('dancing')) {
            anim.dancing = true;
        } else if (!cl.contains('dancing')) {
            // keep dancing state if previously set via triggerDance
        }
        if (cl.contains('jumping') && !anim.jumpActive) {
            anim.jumpT = 0;
            anim.jumpActive = true;
        }
        if (!cl.contains('jumping')) anim.jumpActive = false;
        if (cl.contains('spinning') && anim.spinT < 0) {
            anim.spinT = 0;
        }

        /* ── Walking ── */
        anim.isWalking = cl.contains('walking') || cl.contains('running');
        anim.isRunning = cl.contains('running');

        /* ── Expression from mouth class ── */
        const mouthEl = document.getElementById('ariaMouth');
        if (mouthEl) {
            if (mouthEl.classList.contains('smile')) anim.expression = 'smile';
            else if (mouthEl.classList.contains('sad')) anim.expression = 'sad';
            else anim.expression = 'neutral';
        }

        /* ── Limb angles from CSS transform ── */
        const armLEl = document.getElementById('ariaUpperArmLeft');
        const armREl = document.getElementById('ariaUpperArmRight');
        const legLEl = document.getElementById('ariaUpperLegLeft');
        const legREl = document.getElementById('ariaUpperLegRight');
        anim.cssArmL = cssRotateZ(armLEl);
        anim.cssArmR = cssRotateZ(armREl);
        anim.cssLegL = cssRotateZ(legLEl);
        anim.cssLegR = cssRotateZ(legREl);

        /* ── Mood from aria classes ── */
        if (cl.contains('mood-happy')) { anim.moodColor.set(0x5fb3f5); anim.moodIntensity = 0.4; }
        else if (cl.contains('mood-excited')) { anim.moodColor.set(0xffcc00); anim.moodIntensity = 0.6; }
        else if (cl.contains('mood-sad')) { anim.moodColor.set(0x6c7a89); anim.moodIntensity = 0.25; }
        else if (cl.contains('mood-angry')) { anim.moodColor.set(0xe74c3c); anim.moodIntensity = 0.5; }
        else if (cl.contains('mood-calm')) { anim.moodColor.set(0x4caf50); anim.moodIntensity = 0.3; }
        else if (cl.contains('mood-thinking')) { anim.moodColor.set(0x9b59b6); anim.moodIntensity = 0.3; }
        else { anim.moodIntensity = Math.max(0, anim.moodIntensity - 0.01); }
    }

    function cssRotateZ(el) {
        if (!el) return 0;
        const t = el.style.transform || '';
        const m = t.match(/rotate\(([-\d.]+)deg\)/);
        return m ? (parseFloat(m[1]) * Math.PI / 180) : 0;
    }

    /* ╔══════════════════════════════════════════════════════════════════╗
       ║  CHARACTER UPDATE (per-frame)                                     ║
       ╚══════════════════════════════════════════════════════════════════╝ */
    function updateCharacter(char, anim, dt, mouse2D, camera) {
        /* ── Smooth position ── */
        const speed = 2.8;
        anim.charX += (anim.targetX - anim.charX) * Math.min(1, speed * dt);
        anim.charZ += (anim.targetZ - anim.charZ) * Math.min(1, speed * dt);
        char.root.position.x = anim.charX;
        char.root.position.z = anim.charZ;

        /* ── Mood light ── */
        char.moodLight.color.copy(anim.moodColor);
        char.moodLight.intensity += (anim.moodIntensity - char.moodLight.intensity) * 0.08;

        /* ── Facing direction ── */
        const dx = anim.targetX - anim.charX;
        if (Math.abs(dx) > 0.05) {
            const targetRY = dx > 0 ? -0.28 : 0.28;
            char.root.rotation.y += (targetRY - char.root.rotation.y) * 0.12;
        }

        /* ── Idle breathing ── */
        anim.idleTimer += dt;
        const breathe = Math.sin(anim.idleTimer * 1.15) * 0.012;
        char.torsoGroup.position.y = 0.82 + breathe;
        char.torsoGroup.scale.y = 1 + breathe * 0.4;

        /* ── Blink ── */
        updateBlink(char, anim, dt);

        /* ── Eye tracking ── */
        updateEyeTracking(char, anim, mouse2D, camera);

        /* ── Animations ── */
        if (anim.isWalking) {
            updateWalk(char, anim, dt);
        } else if (anim.dancing) {
            updateDance(char, anim, dt);
        } else if (anim.jumpT >= 0) {
            updateJump(char, anim, dt);
        } else if (anim.waveT >= 0) {
            updateWave(char, anim, dt);
        } else if (anim.spinT >= 0) {
            updateSpin(char, anim, dt);
        } else {
            /* Idle limb sway */
            updateIdleLimbs(char, anim);
        }

        /* ── CSS limb override (for manual limb commands) ── */
        if (!anim.isWalking && !anim.dancing && anim.jumpT < 0 && anim.waveT < 0) {
            if (Math.abs(anim.cssArmL) > 0.01) {
                char.shoulderGroupL.children[0].uaGrp.rotation.z = anim.cssArmL;
            }
            if (Math.abs(anim.cssArmR) > 0.01) {
                char.shoulderGroupR.children[0].uaGrp.rotation.z = anim.cssArmR;
            }
        }

        /* ── Expression morphing ── */
        updateExpression(char, anim, dt);

        /* ── Particle drift ── */
        updateParticles(char.root.parent, anim.time, dt);
    }

    /* ── Blink ──────────────────────────────────────────────────────────── */
    function updateBlink(char, anim, dt) {
        anim.blinkTimer += dt * 1000;
        const head = char.headGroup;
        if (!head.eyeL || !head.eyeR) return;

        if (anim.blinkState === 0 && anim.blinkTimer > IDLE_BLINK_INTERVAL * (0.8 + Math.random() * 0.4)) {
            anim.blinkState = 1;
            anim.blinkTimer = 0;
        }
        if (anim.blinkState === 1) {
            const t = Math.min(anim.blinkTimer / 70, 1);
            const lidY = t * 9; // scale Y to 0 = closed
            [head.eyeL, head.eyeR].forEach(e => {
                if (e && e.lid) e.lid.scale.y = Math.max(0.05, 1 - t * 0.95);
            });
            if (t >= 1) { anim.blinkState = 2; anim.blinkTimer = 0; }
        }
        if (anim.blinkState === 2) {
            const t = Math.min(anim.blinkTimer / 90, 1);
            [head.eyeL, head.eyeR].forEach(e => {
                if (e && e.lid) e.lid.scale.y = 0.05 + t * 0.95;
            });
            if (t >= 1) { anim.blinkState = 0; anim.blinkTimer = 0; }
        }
    }

    /* ── Eye tracking ───────────────────────────────────────────────────── */
    function updateEyeTracking(char, anim, mouse2D, camera) {
        const head = char.headGroup;
        if (!head.eyeL || !head.eyeR) return;

        // Max iris travel
        const MAX_IRIS = 0.018;
        const targetIX = mouse2D.x * MAX_IRIS;
        const targetIY = mouse2D.y * MAX_IRIS * 0.55;

        [head.eyeL, head.eyeR].forEach(eye => {
            if (!eye.irisGrp) return;
            eye.irisGrp.position.x += (targetIX - eye.irisGrp.position.x) * 0.12;
            eye.irisGrp.position.y += (targetIY - eye.irisGrp.position.y) * 0.12;
        });

        /* Subtle head follow */
        const headTargetX = -mouse2D.x * 0.06;
        const headTargetY = mouse2D.y * 0.04;
        head.rotation.y += (headTargetX - head.rotation.y) * 0.04;
        head.rotation.x += (headTargetY - head.rotation.x) * 0.04;
    }

    /* ── Idle limbs ─────────────────────────────────────────────────────── */
    function updateIdleLimbs(char, anim) {
        const t = anim.idleTimer;
        /* gentle arm float */
        char.shoulderGroupL.children[0].uaGrp.rotation.x = Math.sin(t * 0.8) * 0.04;
        char.shoulderGroupR.children[0].uaGrp.rotation.x = Math.sin(t * 0.8 + 0.5) * 0.04;
        char.shoulderGroupL.children[0].uaGrp.rotation.z = -0.18 + Math.sin(t * 0.6) * 0.03;
        char.shoulderGroupR.children[0].uaGrp.rotation.z = 0.18 - Math.sin(t * 0.6 + 0.3) * 0.03;
        /* gentle body sway */
        char.torsoGroup.rotation.z = Math.sin(t * 0.5) * 0.015;
    }

    /* ── Walk cycle ─────────────────────────────────────────────────────── */
    function updateWalk(char, anim, dt) {
        const walkSpeed = anim.isRunning ? 5.5 : 3.8;
        anim.walkT += dt * walkSpeed;
        const t = anim.walkT;
        const sw = Math.sin(t);
        const amp = anim.isRunning ? 0.55 : 0.38;

        /* Legs */
        char.legL.ulGrp.rotation.x = sw * amp;
        char.legR.ulGrp.rotation.x = -sw * amp;
        char.legL.llGrp.rotation.x = Math.max(0, sw * amp * 0.55);
        char.legR.llGrp.rotation.x = Math.max(0, -sw * amp * 0.55);

        /* Arms (opposite swing) */
        char.shoulderGroupL.children[0].uaGrp.rotation.x = -sw * amp * 0.7;
        char.shoulderGroupR.children[0].uaGrp.rotation.x = sw * amp * 0.7;

        /* Torso bob */
        char.torsoGroup.position.y = 0.82 + Math.abs(Math.sin(t * 2)) * (anim.isRunning ? 0.05 : 0.03);
        char.torsoGroup.rotation.z = sw * 0.035;
        char.headGroup.rotation.y = sw * 0.06;
    }

    /* ── Dance ──────────────────────────────────────────────────────────── */
    function updateDance(char, anim, dt) {
        anim.danceTimer += dt * 2.8;
        const t = anim.danceTimer;
        const s = Math.sin(t);
        const c = Math.cos(t);
        const s2 = Math.sin(t * 2);
        const s3 = Math.sin(t * 3);

        /* Body dip + sway */
        char.torsoGroup.position.y = 0.82 + Math.abs(s) * 0.12 - 0.06;
        char.torsoGroup.rotation.z = s * 0.22;
        char.torsoGroup.rotation.x = s2 * 0.08;
        char.headGroup.rotation.y = s * 0.18;
        char.headGroup.rotation.z = s * 0.10;

        /* Arms – expressive waves */
        const armL = char.shoulderGroupL.children[0].uaGrp;
        const armR = char.shoulderGroupR.children[0].uaGrp;
        armL.rotation.x = -0.5 + s * 0.45;
        armL.rotation.z = -0.25 + c * 0.35;
        armR.rotation.x = -0.5 - s * 0.45;
        armR.rotation.z = 0.25 - c * 0.35;

        const laL = char.shoulderGroupL.children[0].laGrp;
        const laR = char.shoulderGroupR.children[0].laGrp;
        if (laL) laL.rotation.x = s3 * 0.45;
        if (laR) laR.rotation.x = -s3 * 0.45;

        /* Legs – fun hip hop moves */
        char.legL.ulGrp.rotation.x = s2 * 0.30;
        char.legR.ulGrp.rotation.x = -s2 * 0.30;
        char.legL.llGrp.rotation.x = Math.max(0, s2 * 0.28);
        char.legR.llGrp.rotation.x = Math.max(0, -s2 * 0.28);
        char.hipGroup.rotation.y = s * 0.25;
        char.hipGroup.position.y = 0.82 + Math.abs(s) * 0.08 - 0.04;

        /* Skirt flare */
        char.skirtMesh.rotation.y = t * 1.2;

        /* Entire body bounce */
        char.root.position.y = Math.abs(Math.sin(t * 2)) * 0.08;
    }

    /* ── Jump ───────────────────────────────────────────────────────────── */
    function updateJump(char, anim, dt) {
        const JUMP_DUR = 0.72;
        anim.jumpT += dt;
        const p = anim.jumpT / JUMP_DUR; // 0..1+

        if (p <= 1.0) {
            /* Smooth arc using a parabola */
            const arcH = 0.85; // units
            const arc = 4 * arcH * p * (1 - p);

            /* Squash on launch (p<0.1) and landing (p>0.85) */
            const squash = p < 0.12 ? (1 - p / 0.12 * 0.15) :
                p > 0.82 ? (1 - (p - 0.82) / 0.18 * 0.18) : 1;
            const stretch = p < 0.12 ? 1 + p / 0.12 * 0.2 :
                p > 0.82 ? 1 + (1 - p) / 0.18 * 0.12 : 1.18;

            char.root.position.y = arc;
            char.root.scale.set(squash, stretch, squash);

            /* Arms up on ascent, down on descent */
            const armAngle = p < 0.5 ? -1.2 * p / 0.5 : -1.2 * (1 - p) / 0.5;
            char.shoulderGroupL.children[0].uaGrp.rotation.x = armAngle;
            char.shoulderGroupR.children[0].uaGrp.rotation.x = armAngle;

            /* Legs tuck mid-air */
            const tuck = Math.sin(p * Math.PI) * 0.6;
            char.legL.ulGrp.rotation.x = tuck;
            char.legR.ulGrp.rotation.x = tuck;
            char.legL.llGrp.rotation.x = -tuck * 0.8;
            char.legR.llGrp.rotation.x = -tuck * 0.8;

        } else {
            /* Landing – restore */
            char.root.position.y = 0;
            char.root.scale.set(1, 1, 1);
            resetArmIdle(char);
            resetLegIdle(char);
            anim.jumpT = -1;
        }
    }

    /* ── Wave ───────────────────────────────────────────────────────────── */
    function updateWave(char, anim, dt) {
        const WAVE_DUR = 1.8;
        anim.waveT += dt;
        const p = anim.waveT / WAVE_DUR;

        if (p <= 1.0) {
            /* Wave arm (right) */
            const wave = Math.sin(p * Math.PI * 4) * (1 - p * 0.5) * 0.6;
            const armR = char.shoulderGroupR.children[0].uaGrp;
            armR.rotation.x = -0.9 + wave;
            armR.rotation.z = 0.35;
            if (char.shoulderGroupR.children[0].laGrp)
                char.shoulderGroupR.children[0].laGrp.rotation.x = -0.3 + wave * 0.6;
        } else {
            resetArmIdle(char);
            anim.waveT = -1;
        }
    }

    /* ── Spin ───────────────────────────────────────────────────────────── */
    function updateSpin(char, anim, dt) {
        const SPIN_DUR = 1.0;
        anim.spinT += dt;
        const p = anim.spinT / SPIN_DUR;

        if (p <= 1.0) {
            /* Ease-in-out spin */
            const angle = p < 0.5
                ? 2 * p * p * Math.PI * 2
                : (-1 + (4 - 2 * p) * p) * Math.PI * 2;
            char.root.rotation.y = angle;
            char.root.position.y = Math.sin(p * Math.PI) * 0.12;
        } else {
            char.root.rotation.y = 0.22;
            char.root.position.y = 0;
            anim.spinT = -1;
        }
    }

    /* ── Expression morphing ────────────────────────────────────────────── */
    function updateExpression(char, anim, dt) {
        const head = char.headGroup;
        const mouth = head.mouth;
        if (!mouth || !head.eyebrowL || !head.eyebrowR) return;

        const target = anim.expression;
        const speed = 3.0 * dt;

        switch (target) {
            case 'smile':
            case 'happy': {
                /* Curve mouth up (scale X wider, tilt) */
                mouth.scale.x += (1.3 - mouth.scale.x) * speed;
                mouth.position.y += (-0.077 - mouth.position.y) * speed;
                head.eyebrowL.rotation.z += (0.28 - head.eyebrowL.rotation.z) * speed;
                head.eyebrowR.rotation.z += (-0.28 - head.eyebrowR.rotation.z) * speed;
                head.eyebrowL.position.y += (0.125 - head.eyebrowL.position.y) * speed;
                head.eyebrowR.position.y += (0.125 - head.eyebrowR.position.y) * speed;
                break;
            }
            case 'sad': {
                mouth.scale.x += (0.85 - mouth.scale.x) * speed;
                mouth.rotation.z += (Math.PI - mouth.rotation.z) * speed;
                mouth.position.y += (-0.087 - mouth.position.y) * speed;
                head.eyebrowL.rotation.z += (-0.28 - head.eyebrowL.rotation.z) * speed;
                head.eyebrowR.rotation.z += (0.28 - head.eyebrowR.rotation.z) * speed;
                head.eyebrowL.position.y += (0.105 - head.eyebrowL.position.y) * speed;
                head.eyebrowR.position.y += (0.105 - head.eyebrowR.position.y) * speed;
                break;
            }
            case 'surprised': {
                mouth.scale.set(0.9, 0.7, 1);
                if (head.eyeL && head.eyeL.lid) head.eyeL.lid.scale.y += (1.3 - head.eyeL.lid.scale.y) * speed;
                if (head.eyeR && head.eyeR.lid) head.eyeR.lid.scale.y += (1.3 - head.eyeR.lid.scale.y) * speed;
                head.eyebrowL.position.y += (0.14 - head.eyebrowL.position.y) * speed;
                head.eyebrowR.position.y += (0.14 - head.eyebrowR.position.y) * speed;
                break;
            }
            default: {
                /* neutral – restore */
                mouth.scale.x += (1.0 - mouth.scale.x) * speed;
                mouth.rotation.z += (0 - mouth.rotation.z) * speed;
                mouth.position.y += (-0.077 - mouth.position.y) * speed;
                head.eyebrowL.rotation.z += (0.12 - head.eyebrowL.rotation.z) * speed;
                head.eyebrowR.rotation.z += (-0.12 - head.eyebrowR.rotation.z) * speed;
                head.eyebrowL.position.y += (0.115 - head.eyebrowL.position.y) * speed;
                head.eyebrowR.position.y += (0.115 - head.eyebrowR.position.y) * speed;
            }
        }
    }

    /* ── Floating particles ─────────────────────────────────────────────── */
    function updateParticles(scene, time, dt) {
        if (!scene) return;
        scene.children.forEach(c => {
            if (!c.userData.isParticle) return;
            const pos = c.geometry.attributes.position;
            const base = c.userData.basePos;
            if (!base) return;
            for (let i = 0; i < pos.count; i++) {
                pos.setY(i, base[i * 3 + 1] + Math.sin(time * 0.6 + i * 1.3) * 0.06);
                pos.setX(i, base[i * 3] + Math.cos(time * 0.4 + i * 0.9) * 0.03);
            }
            pos.needsUpdate = true;
        });
    }

    /* ── Helpers ────────────────────────────────────────────────────────── */
    function resetArmIdle(char) {
        char.shoulderGroupL.children[0].uaGrp.rotation.x = 0;
        char.shoulderGroupL.children[0].uaGrp.rotation.z = -0.18;
        char.shoulderGroupR.children[0].uaGrp.rotation.x = 0;
        char.shoulderGroupR.children[0].uaGrp.rotation.z = 0.18;
        if (char.shoulderGroupL.children[0].laGrp)
            char.shoulderGroupL.children[0].laGrp.rotation.x = 0;
        if (char.shoulderGroupR.children[0].laGrp)
            char.shoulderGroupR.children[0].laGrp.rotation.x = 0;
    }

    function resetLegIdle(char) {
        char.legL.ulGrp.rotation.x = 0;
        char.legR.ulGrp.rotation.x = 0;
        char.legL.llGrp.rotation.x = 0;
        char.legR.llGrp.rotation.x = 0;
    }

})(); /* end IIFE */

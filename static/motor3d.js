/**
 * 3D Motor Comparison Visualization
 * Renders two realistic electric motor cutaway models side by side
 * with internal components (stator, rotor, windings, bearings, shaft, fan, terminal box)
 * Parameters driven by quotation engineering data.
 */

let scene, camera, renderer, controls, animationId;
let viz3dInitialized = false;
let showCutaway = true;
let showAnnotations = true;
let autoRotate = false;
let annotationSprites = [];
let motorGroup1, motorGroup2;

function init3DScene() {
    const container = document.getElementById('viz3dContainer');
    if (!container) return;

    if (renderer) {
        cancelAnimationFrame(animationId);
        container.innerHTML = '';
        renderer.dispose();
    }

    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 500);
    camera.position.set(0, 6, 18);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.maxPolarAngle = Math.PI * 0.85;
    controls.minDistance = 6;
    controls.maxDistance = 35;
    controls.target.set(0, 1, 0);

    // Lighting
    scene.add(new THREE.AmbientLight(0x334466, 0.5));

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.0);
    keyLight.position.set(8, 15, 10);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x88aacc, 0.4);
    fillLight.position.set(-8, 5, -5);
    scene.add(fillLight);

    const rimLight = new THREE.PointLight(0x4fc3f7, 0.5, 30);
    rimLight.position.set(0, 10, -8);
    scene.add(rimLight);

    // Ground
    const groundGeo = new THREE.PlaneGeometry(50, 50);
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x0a0e18, roughness: 0.9 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -2.5;
    ground.receiveShadow = true;
    scene.add(ground);

    const grid = new THREE.GridHelper(50, 50, 0x151a30, 0x101525);
    grid.position.y = -2.49;
    scene.add(grid);

    viz3dInitialized = true;
    animate3D();
}

function animate3D() {
    animationId = requestAnimationFrame(animate3D);
    if (autoRotate && motorGroup1 && motorGroup2) {
        motorGroup1.rotation.y += 0.003;
        motorGroup2.rotation.y += 0.003;
    }
    if (controls) controls.update();
    if (renderer && scene && camera) renderer.render(scene, camera);
}

// ========== MOTOR BUILDER ==========

function buildMotor(eng, color, xOffset) {
    const group = new THREE.Group();
    group.position.x = xOffset;

    const copperKg = eng.copper_weight_kg || 30;
    const coils = eng.number_of_coils || 36;
    const oilLitres = eng.oil_quantity_litres || 5;
    const bearingType = eng.bearing_type || '6312';
    const labourHrs = eng.labour_hours || 20;

    // Derive visual sizes from engineering data
    const motorLength = 3.5 + (copperKg / 60) * 1.5;  // 3.5 to 5
    const statorRadius = 1.8 + (copperKg / 80) * 0.6;
    const rotorRadius = statorRadius * 0.55;
    const shaftRadius = 0.18 + (copperKg / 100) * 0.08;
    const windingThickness = 0.15 + (copperKg / 50) * 0.15;
    const slotCount = coils;
    const bearingRadius = 0.3 + (bearingType.includes('63') ? 0.08 : 0);

    const mainColor = new THREE.Color(color);
    const darkColor = mainColor.clone().multiplyScalar(0.3);

    // === HOUSING (outer shell) ===
    const housingGeo = new THREE.CylinderGeometry(statorRadius + 0.3, statorRadius + 0.3, motorLength, 48, 1, !showCutaway);
    const housingMat = new THREE.MeshPhysicalMaterial({
        color: 0x4a4a5a,
        metalness: 0.7,
        roughness: 0.35,
        clearcoat: 0.2,
    });
    const housing = new THREE.Mesh(housingGeo, housingMat);
    housing.rotation.z = Math.PI / 2;
    housing.castShadow = true;

    if (showCutaway) {
        // Create cutaway by clipping top half of geometry
        const clippedHousingGeo = new THREE.CylinderGeometry(statorRadius + 0.3, statorRadius + 0.3, motorLength, 48, 1, false, 0, Math.PI);
        const clippedHousing = new THREE.Mesh(clippedHousingGeo, housingMat);
        clippedHousing.rotation.z = Math.PI / 2;
        clippedHousing.rotation.y = -Math.PI / 2;
        clippedHousing.castShadow = true;
        group.add(clippedHousing);

        // Inner wall visible
        const innerWallMat = new THREE.MeshStandardMaterial({ color: 0x2a2a35, roughness: 0.6, side: THREE.BackSide });
        const innerWall = new THREE.Mesh(clippedHousingGeo.clone(), innerWallMat);
        innerWall.rotation.z = Math.PI / 2;
        innerWall.rotation.y = -Math.PI / 2;
        group.add(innerWall);
    } else {
        group.add(housing);
    }

    // === COOLING FINS ===
    for (let i = 0; i < 12; i++) {
        const finGeo = new THREE.BoxGeometry(motorLength * 0.8, 0.15, 0.04);
        const finMat = new THREE.MeshStandardMaterial({ color: 0x555565, metalness: 0.6, roughness: 0.4 });
        const fin = new THREE.Mesh(finGeo, finMat);
        const angle = (i / 12) * Math.PI + (showCutaway ? Math.PI : 0);
        fin.position.set(0, Math.cos(angle) * (statorRadius + 0.35), Math.sin(angle) * (statorRadius + 0.35));
        fin.rotation.x = angle;
        if (!showCutaway || angle > Math.PI * 0.1) {
            group.add(fin);
        }
    }

    // === STATOR CORE (laminated iron) ===
    const statorGeo = new THREE.CylinderGeometry(statorRadius, statorRadius, motorLength * 0.75, 48, 1, false, 0, showCutaway ? Math.PI : Math.PI * 2);
    const statorMat = new THREE.MeshStandardMaterial({
        color: 0x3d3d50,
        metalness: 0.5,
        roughness: 0.5,
    });
    const stator = new THREE.Mesh(statorGeo, statorMat);
    stator.rotation.z = Math.PI / 2;
    if (showCutaway) stator.rotation.y = -Math.PI / 2;
    group.add(stator);

    // Stator lamination rings (visual detail)
    for (let i = 0; i < 5; i++) {
        const ringGeo = new THREE.TorusGeometry(statorRadius - 0.02, 0.02, 8, 48, showCutaway ? Math.PI : Math.PI * 2);
        const ringMat = new THREE.MeshBasicMaterial({ color: 0x2a2a3a });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.x = -motorLength * 0.3 + i * (motorLength * 0.6 / 4);
        ring.rotation.y = Math.PI / 2;
        if (showCutaway) ring.rotation.z = -Math.PI / 2;
        group.add(ring);
    }

    // === STATOR WINDINGS (copper coils) ===
    const windingColor = mainColor.clone().lerp(new THREE.Color(0xcc6622), 0.3);
    for (let i = 0; i < Math.min(slotCount, 24); i++) {
        const angle = (i / Math.min(slotCount, 24)) * (showCutaway ? Math.PI : Math.PI * 2);
        if (showCutaway && angle < 0.1) continue;

        const coilGeo = new THREE.TorusGeometry(windingThickness, windingThickness * 0.4, 8, 12);
        const coilMat = new THREE.MeshPhysicalMaterial({
            color: windingColor,
            metalness: 0.8,
            roughness: 0.3,
            emissive: windingColor,
            emissiveIntensity: 0.1,
        });
        const coil = new THREE.Mesh(coilGeo, coilMat);
        const r = statorRadius - windingThickness - 0.1;
        coil.position.set(0, Math.cos(angle) * r, Math.sin(angle) * r);
        coil.rotation.x = angle;
        coil.rotation.z = Math.PI / 2;
        group.add(coil);
    }

    // Winding end turns (visible from cutaway)
    if (showCutaway) {
        for (let side = -1; side <= 1; side += 2) {
            const endTurnGeo = new THREE.TorusGeometry(statorRadius * 0.65, windingThickness * 0.6, 12, 24, Math.PI);
            const endTurnMat = new THREE.MeshPhysicalMaterial({
                color: windingColor,
                metalness: 0.7,
                roughness: 0.35,
                emissive: windingColor,
                emissiveIntensity: 0.08,
            });
            const endTurn = new THREE.Mesh(endTurnGeo, endTurnMat);
            endTurn.position.x = side * motorLength * 0.4;
            endTurn.rotation.y = Math.PI / 2;
            endTurn.rotation.z = -Math.PI / 2;
            group.add(endTurn);
        }
    }

    // === ROTOR ===
    const rotorGeo = new THREE.CylinderGeometry(rotorRadius, rotorRadius, motorLength * 0.7, 36, 1, false, 0, showCutaway ? Math.PI : Math.PI * 2);
    const rotorMat = new THREE.MeshStandardMaterial({
        color: 0x4a4a60,
        metalness: 0.6,
        roughness: 0.4,
    });
    const rotor = new THREE.Mesh(rotorGeo, rotorMat);
    rotor.rotation.z = Math.PI / 2;
    if (showCutaway) rotor.rotation.y = -Math.PI / 2;
    group.add(rotor);

    // Rotor bars (squirrel cage)
    const barCount = Math.min(slotCount, 20);
    for (let i = 0; i < barCount; i++) {
        const angle = (i / barCount) * (showCutaway ? Math.PI : Math.PI * 2);
        if (showCutaway && angle < 0.15) continue;
        const barGeo = new THREE.CylinderGeometry(0.04, 0.04, motorLength * 0.65, 6);
        const barMat = new THREE.MeshStandardMaterial({ color: 0xaa7733, metalness: 0.8, roughness: 0.3 });
        const bar = new THREE.Mesh(barGeo, barMat);
        bar.position.set(0, Math.cos(angle) * (rotorRadius - 0.08), Math.sin(angle) * (rotorRadius - 0.08));
        bar.rotation.z = Math.PI / 2;
        group.add(bar);
    }

    // === SHAFT ===
    const shaftGeo = new THREE.CylinderGeometry(shaftRadius, shaftRadius, motorLength * 1.4, 24);
    const shaftMat = new THREE.MeshPhysicalMaterial({
        color: 0x888899,
        metalness: 0.9,
        roughness: 0.2,
        clearcoat: 0.5,
    });
    const shaft = new THREE.Mesh(shaftGeo, shaftMat);
    shaft.rotation.z = Math.PI / 2;
    shaft.castShadow = true;
    group.add(shaft);

    // === BEARINGS ===
    for (let side = -1; side <= 1; side += 2) {
        const bearingOuterGeo = new THREE.TorusGeometry(bearingRadius, 0.08, 16, 32, showCutaway ? Math.PI : Math.PI * 2);
        const bearingMat = new THREE.MeshPhysicalMaterial({
            color: 0xccccdd,
            metalness: 0.9,
            roughness: 0.15,
        });
        const bearing = new THREE.Mesh(bearingOuterGeo, bearingMat);
        bearing.position.x = side * motorLength * 0.45;
        bearing.rotation.y = Math.PI / 2;
        if (showCutaway) bearing.rotation.z = -Math.PI / 2;
        group.add(bearing);

        // Bearing balls
        const ballCount = 8;
        for (let b = 0; b < ballCount; b++) {
            const bAngle = (b / ballCount) * (showCutaway ? Math.PI : Math.PI * 2);
            if (showCutaway && bAngle < 0.2) continue;
            const ballGeo = new THREE.SphereGeometry(0.04, 12, 12);
            const ballMat = new THREE.MeshPhysicalMaterial({ color: 0xeeeeee, metalness: 0.95, roughness: 0.1 });
            const ball = new THREE.Mesh(ballGeo, ballMat);
            ball.position.set(
                side * motorLength * 0.45,
                Math.cos(bAngle) * bearingRadius,
                Math.sin(bAngle) * bearingRadius
            );
            group.add(ball);
        }
    }

    // === END BELLS ===
    for (let side = -1; side <= 1; side += 2) {
        const bellGeo = new THREE.CylinderGeometry(statorRadius + 0.3, statorRadius * 0.7, 0.3, 48, 1, false, 0, showCutaway ? Math.PI : Math.PI * 2);
        const bellMat = new THREE.MeshStandardMaterial({ color: 0x4a4a5a, metalness: 0.6, roughness: 0.4 });
        const bell = new THREE.Mesh(bellGeo, bellMat);
        bell.position.x = side * motorLength * 0.52;
        bell.rotation.z = side * Math.PI / 2;
        if (showCutaway) bell.rotation.y = -Math.PI / 2;
        bell.castShadow = true;
        group.add(bell);
    }

    // === FAN (drive end) ===
    const fanGroup = new THREE.Group();
    fanGroup.position.x = -motorLength * 0.7;
    for (let i = 0; i < 6; i++) {
        const angle = (i / 6) * Math.PI * 2;
        const bladeGeo = new THREE.BoxGeometry(0.05, 0.6, 0.25);
        const bladeMat = new THREE.MeshStandardMaterial({ color: 0x333340, roughness: 0.5 });
        const blade = new THREE.Mesh(bladeGeo, bladeMat);
        blade.position.set(0, Math.cos(angle) * 0.5, Math.sin(angle) * 0.5);
        blade.rotation.x = angle + 0.3;
        fanGroup.add(blade);
    }
    // Fan shroud
    const shroudGeo = new THREE.CylinderGeometry(0.9, 0.9, 0.4, 24, 1, true);
    const shroudMat = new THREE.MeshStandardMaterial({ color: 0x3a3a45, metalness: 0.5, roughness: 0.4, side: THREE.DoubleSide });
    const shroud = new THREE.Mesh(shroudGeo, shroudMat);
    shroud.rotation.z = Math.PI / 2;
    fanGroup.add(shroud);
    group.add(fanGroup);

    // === TERMINAL BOX ===
    const termBoxGeo = new THREE.BoxGeometry(0.8, 0.5, 0.6);
    const termBoxMat = new THREE.MeshStandardMaterial({ color: 0x3a3a4a, metalness: 0.5, roughness: 0.4 });
    const termBox = new THREE.Mesh(termBoxGeo, termBoxMat);
    termBox.position.set(0, statorRadius + 0.5, 0);
    termBox.castShadow = true;
    if (!showCutaway) group.add(termBox);

    // === OIL/COOLANT INDICATOR (translucent ring if oil present) ===
    if (oilLitres > 0) {
        const oilLevel = Math.min(oilLitres / 15, 1);
        const oilGeo = new THREE.CylinderGeometry(statorRadius - 0.05, statorRadius - 0.05, motorLength * 0.7 * oilLevel, 32, 1, false, Math.PI, showCutaway ? Math.PI : Math.PI * 2);
        const oilMat = new THREE.MeshPhysicalMaterial({
            color: 0x88aa22,
            transparent: true,
            opacity: 0.2,
            roughness: 0.1,
            transmission: 0.5,
        });
        const oil = new THREE.Mesh(oilGeo, oilMat);
        oil.rotation.z = Math.PI / 2;
        oil.position.y = -(statorRadius * 0.3) * (1 - oilLevel);
        if (showCutaway) {
            oil.rotation.y = -Math.PI / 2;
            group.add(oil);
        }
    }

    // === COLOR ACCENT (glowing edge ring) ===
    const accentGeo = new THREE.TorusGeometry(statorRadius + 0.32, 0.03, 8, 48);
    const accentMat = new THREE.MeshBasicMaterial({ color: mainColor, transparent: true, opacity: 0.6 });
    const accent1 = new THREE.Mesh(accentGeo, accentMat);
    accent1.position.x = motorLength * 0.5;
    accent1.rotation.y = Math.PI / 2;
    group.add(accent1);
    const accent2 = accent1.clone();
    accent2.position.x = -motorLength * 0.5;
    group.add(accent2);

    group.position.y = 0;
    return group;
}

// ========== ANNOTATIONS ==========

function addAnnotations(group, eng, color, side) {
    if (!showAnnotations) return;
    const c = new THREE.Color(color);
    const hex = '#' + c.getHexString();
    const labels = [
        { text: `Copper: ${eng.copper_weight_kg || '?'} Kg`, pos: [0, 2.2, 0] },
        { text: `Coils: ${eng.number_of_coils || '?'}`, pos: [0, 1.6, 1.5] },
        { text: `Wire: ${eng.wire_gauge || '?'}`, pos: [1.5, 1.8, 0] },
        { text: `Bearing: ${eng.bearing_type || '?'}`, pos: [-1.5, -0.5, 0] },
        { text: `Oil: ${eng.oil_quantity_litres || 0}L`, pos: [0, -1.5, 0] },
    ];

    labels.forEach(l => {
        const sprite = createLabel(l.text, hex);
        sprite.position.set(l.pos[0] + group.position.x, l.pos[1], l.pos[2]);
        sprite.userData.vizObject = true;
        sprite.userData.annotation = true;
        scene.add(sprite);
        annotationSprites.push(sprite);
    });
}

function createLabel(text, color) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 300;
    canvas.height = 48;

    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.roundRect(0, 4, canvas.width, 40, 6);
    ctx.fill();

    ctx.font = 'bold 20px monospace';
    ctx.fillStyle = color || '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 150, 24);

    const texture = new THREE.CanvasTexture(canvas);
    const mat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(3, 0.5, 1);
    return sprite;
}

// ========== CONTROLS ==========

function toggleCutawayView() {
    showCutaway = document.getElementById('toggleCutaway').checked;
    render3DVisualization();
}

function toggleAnnotations() {
    showAnnotations = document.getElementById('toggleLabels').checked;
    annotationSprites.forEach(s => { s.visible = showAnnotations; });
}

function toggleAutoRotate() {
    autoRotate = document.getElementById('toggleRotate').checked;
}

// ========== MAIN RENDER ==========

function render3DVisualization() {
    if (!compareData[1] || !compareData[2]) return;

    // The viz3dSection is visible when comparisonRow is shown
    if (!viz3dInitialized) init3DScene();

    // Clear previous motors
    if (motorGroup1) { scene.remove(motorGroup1); }
    if (motorGroup2) { scene.remove(motorGroup2); }
    annotationSprites.forEach(s => scene.remove(s));
    annotationSprites = [];

    const eng1 = compareData[1].engineering_details || {};
    const eng2 = compareData[2].engineering_details || {};

    // Build two motors side by side
    motorGroup1 = buildMotor(eng1, 0x4fc3f7, -5);
    motorGroup2 = buildMotor(eng2, 0xff8a65, 5);
    scene.add(motorGroup1);
    scene.add(motorGroup2);

    // Annotations
    addAnnotations(motorGroup1, eng1, 0x4fc3f7, 'left');
    addAnnotations(motorGroup2, eng2, 0xff8a65, 'right');

    // Update UI labels
    const q1 = compareData[1], q2 = compareData[2];
    document.getElementById('motor1Title').textContent = q1.quotation_number + ' — ' + ((q1.motor_details || {}).manufacturer || '');
    document.getElementById('motor2Title').textContent = q2.quotation_number + ' — ' + ((q2.motor_details || {}).manufacturer || '');

    // Specs panels
    const m1 = q1.motor_details || {};
    const m2 = q2.motor_details || {};
    document.getElementById('spec1Header').textContent = q1.quotation_number;
    document.getElementById('spec1Body').innerHTML = `
        ${m1.power ? m1.power + ' kW' : 'N/A'} · ${m1.voltage || '?'}V · ${m1.rpm || '?'} RPM<br>
        Copper: ${eng1.copper_weight_kg || '?'} Kg · Coils: ${eng1.number_of_coils || '?'} · ${eng1.wire_gauge || '?'}<br>
        Oil: ${eng1.oil_quantity_litres || 0}L · Labour: ${eng1.labour_hours || '?'}h · Confidence: ${eng1.overall_confidence || '?'}%
    `;
    document.getElementById('spec2Header').textContent = q2.quotation_number;
    document.getElementById('spec2Body').innerHTML = `
        ${m2.power ? m2.power + ' kW' : 'N/A'} · ${m2.voltage || '?'}V · ${m2.rpm || '?'} RPM<br>
        Copper: ${eng2.copper_weight_kg || '?'} Kg · Coils: ${eng2.number_of_coils || '?'} · ${eng2.wire_gauge || '?'}<br>
        Oil: ${eng2.oil_quantity_litres || 0}L · Labour: ${eng2.labour_hours || '?'}h · Confidence: ${eng2.overall_confidence || '?'}%
    `;

    camera.position.set(0, 6, 18);
    controls.target.set(0, 0, 0);
}

// Handle resize
window.addEventListener('resize', () => {
    if (!renderer || !camera) return;
    const container = document.getElementById('viz3dContainer');
    if (!container) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});

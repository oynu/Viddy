import React, { useEffect, useRef } from 'react';

interface TrailPoint {
  x: number;
  y: number;
  vx: number;
  vy: number;
  speed: number;
  time: number;
  alpha: number;
}

interface VortexSpark {
  x: number;
  y: number;
  vx: number;
  vy: number;
  swirl: number;
  alpha: number;
  life: number;
  maxLife: number;
  size: number;
  hue: 'purple' | 'white' | 'violet';
}

interface ShockwaveRing {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  alpha: number;
}

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface Face3D {
  indices: number[];
  tint: 'purple' | 'white' | 'violet';
  baseAlpha: number;
}

interface InteractiveBody3D {
  mesh: { vertices: Point3D[]; faces: Face3D[] };
  anchorX: number; // fraction of screen width
  anchorY: number; // fraction of screen height
  offsetX: number;
  offsetY: number;
  vx: number;
  vy: number;
  rotX: number;
  rotY: number;
  rotZ: number;
  rvX: number;
  rvY: number;
  rvZ: number;
  baseScale: number;
  scalePulse: number;
  floatPhase: number;
}

interface GlassBubble {
  x: number;
  y: number;
  vx: number;
  vy: number;
  baseRadius: number;
  wobblePhase: number;
  wobbleSpeed: number;
  hue: 'purple' | 'white';
}

export const LiquidGlassCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Cursor & Spring Follower Physics
    let targetX = width / 2;
    let targetY = height * 0.38;
    let mouseX = targetX;
    let mouseY = targetY;
    let cursorVX = 0;
    let cursorVY = 0;

    // Secondary playful spring-chaser orb
    let chaserX = targetX;
    let chaserY = targetY;
    let chaserVX = 0;
    let chaserVY = 0;

    let lastEventX = targetX;
    let lastEventY = targetY;
    let hasMoved = false;

    const trail: TrailPoint[] = [];
    const maxTrailLength = 46;
    const sparks: VortexSpark[] = [];
    const shockwaves: ShockwaveRing[] = [];

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // -----------------------------------------------------------------
    // Mesh Builders: 3D Torus Ring, Geodesic Crystal & Star Polyhedron
    // -----------------------------------------------------------------
    const createTorusMesh = (majorR: number, minorR: number, uSteps: number, vSteps: number) => {
      const vertices: Point3D[] = [];
      const faces: Face3D[] = [];
      const tints: Array<'purple' | 'white' | 'violet'> = ['purple', 'white', 'violet'];

      for (let i = 0; i < uSteps; i++) {
        const u = (i / uSteps) * Math.PI * 2;
        for (let j = 0; j < vSteps; j++) {
          const v = (j / vSteps) * Math.PI * 2;
          const x = (majorR + minorR * Math.cos(v)) * Math.cos(u);
          const y = (majorR + minorR * Math.cos(v)) * Math.sin(u);
          const z = minorR * Math.sin(v);
          vertices.push({ x, y, z });
        }
      }

      for (let i = 0; i < uSteps; i++) {
        const nextI = (i + 1) % uSteps;
        for (let j = 0; j < vSteps; j++) {
          const nextJ = (j + 1) % vSteps;
          const a = i * vSteps + j;
          const b = nextI * vSteps + j;
          const c = nextI * vSteps + nextJ;
          const d = i * vSteps + nextJ;

          const tint = tints[(i + j) % 3];
          faces.push({ indices: [a, b, c], tint, baseAlpha: 0.065 });
          faces.push({ indices: [a, c, d], tint, baseAlpha: 0.065 });
        }
      }
      return { vertices, faces };
    };

    const createCrownCrystal = (radius: number, heightScale: number, segments = 9) => {
      const vertices: Point3D[] = [];
      const faces: Face3D[] = [];
      vertices.push({ x: 0, y: -radius * heightScale, z: 0 });
      vertices.push({ x: 0, y: radius * heightScale, z: 0 });

      for (let i = 0; i < segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        vertices.push({
          x: Math.cos(theta) * radius,
          y: -radius * 0.26,
          z: Math.sin(theta) * radius
        });
      }
      for (let i = 0; i < segments; i++) {
        const theta = ((i + 0.5) / segments) * Math.PI * 2;
        vertices.push({
          x: Math.cos(theta) * radius * 0.9,
          y: radius * 0.26,
          z: Math.sin(theta) * radius * 0.9
        });
      }

      const tints: Array<'purple' | 'white' | 'violet'> = ['purple', 'white', 'violet'];
      for (let i = 0; i < segments; i++) {
        const next = (i + 1) % segments;
        const u0 = 2 + i;
        const u1 = 2 + next;
        const l0 = 2 + segments + i;
        const l1 = 2 + segments + ((i + segments - 1) % segments);

        faces.push({ indices: [0, u0, u1], tint: tints[i % 3], baseAlpha: 0.07 });
        faces.push({ indices: [u0, l0, u1], tint: tints[(i + 1) % 3], baseAlpha: 0.085 });
        faces.push({ indices: [u0, l1, l0], tint: tints[(i + 2) % 3], baseAlpha: 0.075 });
        faces.push({ indices: [1, l0, l1], tint: tints[i % 3], baseAlpha: 0.065 });
      }
      return { vertices, faces };
    };

    // 4 Interactive 3D Physics Bodies that respond to the cursor
    const bodies: InteractiveBody3D[] = [
      // 1. Center-Top Floating 3D Liquid Glass Torus (Donut)
      {
        mesh: createTorusMesh(115, 38, 16, 8),
        anchorX: 0.5,
        anchorY: 0.25,
        offsetX: 0,
        offsetY: 0,
        vx: 0,
        vy: 0,
        rotX: 0.9,
        rotY: 0.3,
        rotZ: 0,
        rvX: 0.004,
        rvY: 0.007,
        rvZ: 0.003,
        baseScale: 1.15,
        scalePulse: 0,
        floatPhase: 0
      },
      // 2. Right Playful Crown Gem
      {
        mesh: createCrownCrystal(78, 1.35, 8),
        anchorX: 0.84,
        anchorY: 0.38,
        offsetX: 0,
        offsetY: 0,
        vx: 0,
        vy: 0,
        rotX: 0.3,
        rotY: 0.5,
        rotZ: -0.2,
        rvX: -0.005,
        rvY: 0.008,
        rvZ: 0.004,
        baseScale: 1.05,
        scalePulse: 0,
        floatPhase: 2.1
      },
      // 3. Left Playful Crown Gem
      {
        mesh: createCrownCrystal(74, 1.4, 7),
        anchorX: 0.15,
        anchorY: 0.52,
        offsetX: 0,
        offsetY: 0,
        vx: 0,
        vy: 0,
        rotX: -0.2,
        rotY: 0.2,
        rotZ: 0.3,
        rvX: 0.006,
        rvY: -0.006,
        rvZ: 0.003,
        baseScale: 1.0,
        scalePulse: 0,
        floatPhase: 4.2
      },
      // 4. Lower-Right Mini Orbiting Torus
      {
        mesh: createTorusMesh(62, 22, 12, 6),
        anchorX: 0.78,
        anchorY: 0.74,
        offsetX: 0,
        offsetY: 0,
        vx: 0,
        vy: 0,
        rotX: 1.1,
        rotY: -0.4,
        rotZ: 0.2,
        rvX: 0.007,
        rvY: -0.005,
        rvZ: 0.005,
        baseScale: 0.95,
        scalePulse: 0,
        floatPhase: 1.3
      }
    ];

    // -----------------------------------------------------------------
    // Playful Bouncing 3D Liquid Glass Bubbles
    // -----------------------------------------------------------------
    const bubbles: GlassBubble[] = Array.from({ length: 11 }, (_, idx) => ({
      x: Math.random() * width,
      y: Math.random() * height * 0.85,
      vx: (Math.random() - 0.5) * 0.7,
      vy: (Math.random() - 0.5) * 0.7,
      baseRadius: Math.random() * 26 + 16,
      wobblePhase: Math.random() * Math.PI * 2,
      wobbleSpeed: Math.random() * 0.04 + 0.025,
      hue: idx % 2 === 0 ? 'purple' : 'white'
    }));

    // -----------------------------------------------------------------
    // Pointer Move & Click Handlers (Velocity + Vortex Sparks + Ripples)
    // -----------------------------------------------------------------
    const handlePointerMove = (e: PointerEvent) => {
      const dx = e.clientX - lastEventX;
      const dy = e.clientY - lastEventY;
      const dist = Math.hypot(dx, dy);
      const speed = Math.min(60, dist);

      targetX = e.clientX;
      targetY = e.clientY;
      cursorVX = dx;
      cursorVY = dy;
      hasMoved = true;

      const now = performance.now();
      trail.push({
        x: e.clientX,
        y: e.clientY,
        vx: dx * 0.15,
        vy: dy * 0.15,
        speed,
        time: now,
        alpha: 1.0
      });

      if (trail.length > maxTrailLength) {
        trail.shift();
      }

      // Spawn playful swirling vortex sparks based on cursor momentum
      if (dist > 4 && sparks.length < 95) {
        const count = Math.min(4, Math.ceil(dist / 9));
        const hues: Array<'purple' | 'white' | 'violet'> = ['purple', 'white', 'violet'];
        for (let i = 0; i < count; i++) {
          const spreadAngle = (Math.random() - 0.5) * 1.4;
          const baseAngle = Math.atan2(dy, dx) + spreadAngle;
          const sparkSpeed = Math.min(5.5, dist * 0.12 + Math.random() * 1.6);
          sparks.push({
            x: e.clientX + (Math.random() - 0.5) * 10,
            y: e.clientY + (Math.random() - 0.5) * 10,
            vx: Math.cos(baseAngle) * sparkSpeed * 0.45 + (Math.random() - 0.5) * 1.2,
            vy: Math.sin(baseAngle) * sparkSpeed * 0.45 + (Math.random() - 0.5) * 1.2,
            swirl: (Math.random() - 0.5) * 0.14,
            alpha: 1.0,
            life: 0,
            maxLife: Math.random() * 34 + 22,
            size: Math.random() * 2.5 + 1.0,
            hue: hues[Math.floor(Math.random() * hues.length)]
          });
        }
      }

      // Fast cursor whip spawns a mini shockwave ripple automatically
      if (dist > 42 && shockwaves.length < 5) {
        shockwaves.push({
          x: e.clientX,
          y: e.clientY,
          radius: 8,
          maxRadius: 140,
          alpha: 0.45
        });
      }

      lastEventX = e.clientX;
      lastEventY = e.clientY;
    };

    const handlePointerDown = (e: PointerEvent) => {
      // Spawn an expanding 3D shockwave ring on click
      shockwaves.push({
        x: e.clientX,
        y: e.clientY,
        radius: 10,
        maxRadius: 260,
        alpha: 0.85
      });

      // Burst of playful vortex particles
      const hues: Array<'purple' | 'white' | 'violet'> = ['purple', 'white', 'violet'];
      for (let i = 0; i < 18; i++) {
        const angle = (i / 18) * Math.PI * 2 + Math.random() * 0.2;
        const speed = Math.random() * 4.5 + 2.0;
        sparks.push({
          x: e.clientX,
          y: e.clientY,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          swirl: (Math.random() - 0.5) * 0.18,
          alpha: 1.0,
          life: 0,
          maxLife: Math.random() * 38 + 25,
          size: Math.random() * 3.0 + 1.2,
          hue: hues[i % 3]
        });
      }

      // Impulse push on nearby 3D bodies
      for (const body of bodies) {
        const bx = width * body.anchorX + body.offsetX;
        const by = height * body.anchorY + body.offsetY;
        const dx = bx - e.clientX;
        const dy = by - e.clientY;
        const d = Math.hypot(dx, dy) || 1;
        if (d < 450) {
          const force = ((450 - d) / 450) * 18;
          body.vx += (dx / d) * force;
          body.vy += (dy / d) * force;
          body.rvX += (Math.random() - 0.5) * 0.08;
          body.rvY += (Math.random() - 0.5) * 0.08;
          body.scalePulse = 0.22;
        }
      }
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerdown', handlePointerDown);

    let timeTick = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // 1. Update Cursor & Spring Chaser Physics
      mouseX += (targetX - mouseX) * 0.22;
      mouseY += (targetY - mouseY) * 0.22;

      const springK = 0.085;
      const damping = 0.78;
      chaserVX = (chaserVX + (targetX - chaserX) * springK) * damping;
      chaserVY = (chaserVY + (targetY - chaserY) * springK) * damping;
      chaserX += chaserVX;
      chaserY += chaserVY;

      cursorVX *= 0.88;
      cursorVY *= 0.88;

      const parallaxX = (mouseX - width / 2) * 0.055;
      const parallaxY = (mouseY - height / 2) * 0.055;

      if (!prefersReducedMotion) {
        timeTick += 0.022;
      }

      // -------------------------------------------------------------
      // A. Render Cursor-Reactive 3D Elastic Wave Floor Grid
      // -------------------------------------------------------------
      const horizonY = height * 0.68 + parallaxY * 0.28;
      ctx.save();
      const cols = 20;
      const rows = 12;

      const getGridPoint = (c: number, r: number) => {
        const normalizedC = c / cols;
        const t = r / rows;
        const depthFactor = Math.pow(t, 2.05);
        const spread = width * 1.5;
        const xBase = width / 2 + parallaxX * 0.7 + normalizedC * spread * depthFactor;
        const yBase = horizonY + depthFactor * (height - horizonY);

        // Organic wave + interactive cursor gravity ripple on the floor
        const wave =
          Math.sin(normalizedC * 6 + timeTick * 1.6 + t * 4.5) * 11 * depthFactor;
        const distToMouse = Math.hypot(xBase - mouseX, yBase - mouseY);
        const cursorRipple =
          distToMouse < 260
            ? Math.cos((distToMouse / 260) * Math.PI * 0.5) *
              Math.sin(timeTick * 5 - distToMouse * 0.04) *
              22 *
              depthFactor
            : 0;

        return { x: xBase, y: yBase + wave + cursorRipple, depthFactor, distToMouse };
      };

      // Longitudinal lines
      for (let c = -cols; c <= cols; c++) {
        ctx.beginPath();
        for (let r = 0; r <= rows; r++) {
          const pt = getGridPoint(c, r);
          if (r === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        const grad = ctx.createLinearGradient(0, horizonY, 0, height);
        grad.addColorStop(0, 'rgba(168, 85, 247, 0)');
        grad.addColorStop(0.45, 'rgba(168, 85, 247, 0.09)');
        grad.addColorStop(1, 'rgba(255, 255, 255, 0.14)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Transverse wave lines
      for (let r = 1; r <= rows; r++) {
        ctx.beginPath();
        for (let c = -cols; c <= cols; c++) {
          const pt = getGridPoint(c, r);
          if (c === -cols) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        const depthFactor = Math.pow(r / rows, 2.05);
        const alpha = depthFactor * 0.16;
        ctx.strokeStyle =
          r % 2 === 0
            ? `rgba(192, 132, 252, ${alpha})`
            : `rgba(255, 255, 255, ${alpha * 0.8})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      ctx.restore();

      // -------------------------------------------------------------
      // B. Render Playful Bouncing 3D Liquid Glass Bubbles
      // -------------------------------------------------------------
      ctx.save();
      for (const b of bubbles) {
        b.wobblePhase += b.wobbleSpeed;
        b.x += b.vx;
        b.y += b.vy;

        // Soft screen wrap
        if (b.x < -60) b.x = width + 60;
        if (b.x > width + 60) b.x = -60;
        if (b.y < -60) b.y = height + 60;
        if (b.y > height + 60) b.y = -60;

        // Playful cursor repulsion on bubbles
        const dx = b.x - mouseX;
        const dy = b.y - mouseY;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 170) {
          const push = ((170 - dist) / 170) * 0.85;
          b.vx += (dx / dist) * push;
          b.vy += (dy / dist) * push;
        }

        // Damping back to gentle drift
        b.vx *= 0.97;
        b.vy *= 0.97;
        if (Math.hypot(b.vx, b.vy) < 0.25) {
          b.vx += (Math.random() - 0.5) * 0.08;
          b.vy += (Math.random() - 0.5) * 0.08;
        }

        const rx = b.baseRadius * (1 + Math.sin(b.wobblePhase) * 0.08);
        const ry = b.baseRadius * (1 + Math.cos(b.wobblePhase) * 0.08);

        const grad = ctx.createRadialGradient(
          b.x - rx * 0.35,
          b.y - ry * 0.35,
          rx * 0.1,
          b.x,
          b.y,
          rx
        );
        if (b.hue === 'purple') {
          grad.addColorStop(0, 'rgba(255, 255, 255, 0.45)');
          grad.addColorStop(0.35, 'rgba(192, 132, 252, 0.18)');
          grad.addColorStop(0.85, 'rgba(124, 58, 237, 0.06)');
          grad.addColorStop(1, 'rgba(168, 85, 247, 0.28)');
        } else {
          grad.addColorStop(0, 'rgba(255, 255, 255, 0.5)');
          grad.addColorStop(0.4, 'rgba(255, 255, 255, 0.12)');
          grad.addColorStop(0.85, 'rgba(192, 132, 252, 0.05)');
          grad.addColorStop(1, 'rgba(255, 255, 255, 0.25)');
        }

        ctx.fillStyle = grad;
        ctx.strokeStyle =
          b.hue === 'purple' ? 'rgba(216, 180, 254, 0.35)' : 'rgba(255, 255, 255, 0.35)';
        ctx.lineWidth = 1;

        ctx.beginPath();
        ctx.ellipse(b.x, b.y, rx, ry, b.wobblePhase * 0.25, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Crisp liquid glass specular glint
        ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
        ctx.beginPath();
        ctx.ellipse(
          b.x - rx * 0.35,
          b.y - ry * 0.35,
          rx * 0.18,
          ry * 0.09,
          -Math.PI / 4,
          0,
          Math.PI * 2
        );
        ctx.fill();
      }
      ctx.restore();

      // -------------------------------------------------------------
      // C. Render Interactive 3D Physics-Driven Glass Bodies
      // -------------------------------------------------------------
      const fov = 480;
      for (const body of bodies) {
        const homeX = width * body.anchorX + parallaxX * 1.1;
        const homeY =
          height * body.anchorY +
          parallaxY * 1.1 +
          Math.sin(timeTick * 1.2 + body.floatPhase) * 14;

        const curX = homeX + body.offsetX;
        const curY = homeY + body.offsetY;

        // Cursor proximity interaction: playful nudge + spin boost!
        const dx = curX - mouseX;
        const dy = curY - mouseY;
        const dist = Math.hypot(dx, dy) || 1;
        const interactRadius = 230;

        if (dist < interactRadius && hasMoved) {
          const factor = (interactRadius - dist) / interactRadius;
          // Gentle elastic push + rotational spin from cursor velocity
          body.vx += (dx / dist) * factor * 0.9 + cursorVX * factor * 0.06;
          body.vy += (dy / dist) * factor * 0.9 + cursorVY * factor * 0.06;
          body.rvY += cursorVX * factor * 0.00045;
          body.rvX -= cursorVY * factor * 0.00045;
          body.scalePulse = Math.max(body.scalePulse, factor * 0.14);
        }

        // Spring-damper return to anchor
        body.vx = (body.vx - body.offsetX * 0.045) * 0.88;
        body.vy = (body.vy - body.offsetY * 0.045) * 0.88;
        body.offsetX += body.vx;
        body.offsetY += body.vy;

        // Smooth angular velocity decay toward base idle rotation
        body.rvX = body.rvX * 0.97 + 0.0035 * 0.03;
        body.rvY = body.rvY * 0.97 + 0.006 * 0.03;
        body.rvZ = body.rvZ * 0.97 + 0.0025 * 0.03;

        body.rotX += body.rvX;
        body.rotY += body.rvY;
        body.rotZ += body.rvZ;
        body.scalePulse *= 0.92;

        const cx = homeX + body.offsetX;
        const cy = homeY + body.offsetY;
        const scale = body.baseScale + body.scalePulse;

        // Ambient Purple-White Glow behind 3D body
        ctx.save();
        const haloGrad = ctx.createRadialGradient(cx, cy, 4, cx, cy, 155 * scale);
        haloGrad.addColorStop(0, 'rgba(168, 85, 247, 0.24)');
        haloGrad.addColorStop(0.5, 'rgba(124, 58, 237, 0.07)');
        haloGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = haloGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, 155 * scale, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        // Transform vertices
        const transformed = body.mesh.vertices.map(v => {
          const y1 = v.y * Math.cos(body.rotX) - v.z * Math.sin(body.rotX);
          const z1 = v.y * Math.sin(body.rotX) + v.z * Math.cos(body.rotX);
          const x2 = v.x * Math.cos(body.rotY) + z1 * Math.sin(body.rotY);
          const z2 = -v.x * Math.sin(body.rotY) + z1 * Math.cos(body.rotY);
          const x3 = x2 * Math.cos(body.rotZ) - y1 * Math.sin(body.rotZ);
          const y3 = x2 * Math.sin(body.rotZ) + y1 * Math.cos(body.rotZ);

          const perspective = fov / (fov + z2 + 250);
          return {
            x: cx + x3 * perspective * scale,
            y: cy + y3 * perspective * scale,
            z: z2,
            rawX: x3,
            rawY: y3,
            rawZ: z2
          };
        });

        // Dynamic light vector from cursor
        const lx = mouseX - cx;
        const ly = mouseY - cy;
        const lz = -290;
        const lLen = Math.hypot(lx, ly, lz) || 1;
        const normLX = lx / lLen;
        const normLY = ly / lLen;
        const normLZ = lz / lLen;

        // Painter's Algorithm Z-sort
        const sortedFaces = body.mesh.faces
          .map(face => {
            const v0 = transformed[face.indices[0]];
            const v1 = transformed[face.indices[1]];
            const v2 = transformed[face.indices[2]];
            return { face, v0, v1, v2, avgZ: (v0.z + v1.z + v2.z) / 3 };
          })
          .sort((a, b) => b.avgZ - a.avgZ);

        ctx.save();
        for (const { face, v0, v1, v2 } of sortedFaces) {
          const ax = v1.rawX - v0.rawX;
          const ay = v1.rawY - v0.rawY;
          const az = v1.rawZ - v0.rawZ;
          const bx = v2.rawX - v0.rawX;
          const by = v2.rawY - v0.rawY;
          const bz = v2.rawZ - v0.rawZ;

          let nx = ay * bz - az * by;
          let ny = az * bx - ax * bz;
          let nz = ax * by - ay * bx;
          const nLen = Math.hypot(nx, ny, nz) || 1;
          nx /= nLen;
          ny /= nLen;
          nz /= nLen;

          const dot = Math.max(0, nx * normLX + ny * normLY + nz * normLZ);
          const specular = Math.pow(dot, 4);
          const isFront = nz < 0;

          const fillAlpha = isFront
            ? face.baseAlpha + specular * 0.36 + dot * 0.11
            : face.baseAlpha * 0.32;
          const strokeAlpha = isFront ? 0.24 + specular * 0.48 : 0.06;

          if (face.tint === 'purple') {
            ctx.fillStyle = `rgba(168, 85, 247, ${fillAlpha})`;
            ctx.strokeStyle = `rgba(216, 180, 254, ${strokeAlpha})`;
          } else if (face.tint === 'violet') {
            ctx.fillStyle = `rgba(124, 58, 237, ${fillAlpha})`;
            ctx.strokeStyle = `rgba(192, 132, 252, ${strokeAlpha})`;
          } else {
            ctx.fillStyle = `rgba(255, 255, 255, ${fillAlpha * 0.92})`;
            ctx.strokeStyle = `rgba(255, 255, 255, ${strokeAlpha})`;
          }

          ctx.lineWidth = isFront ? 1.2 : 0.6;
          ctx.beginPath();
          ctx.moveTo(v0.x, v0.y);
          ctx.lineTo(v1.x, v1.y);
          ctx.lineTo(v2.x, v2.y);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }
        ctx.restore();
      }

      // -------------------------------------------------------------
      // D. Expanding 3D Shockwave Ripples (On Click or Fast Whip)
      // -------------------------------------------------------------
      if (shockwaves.length > 0) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        for (let i = shockwaves.length - 1; i >= 0; i--) {
          const sw = shockwaves[i];
          sw.radius += (sw.maxRadius - sw.radius) * 0.14;
          sw.alpha *= 0.91;

          if (sw.alpha < 0.02) {
            shockwaves.splice(i, 1);
            continue;
          }

          ctx.strokeStyle = `rgba(216, 180, 254, ${sw.alpha})`;
          ctx.lineWidth = 2.5 * sw.alpha;
          ctx.beginPath();
          ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
          ctx.stroke();

          ctx.strokeStyle = `rgba(255, 255, 255, ${sw.alpha * 0.7})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(sw.x, sw.y, sw.radius * 0.82, 0, Math.PI * 2);
          ctx.stroke();
        }
        ctx.restore();
      }

      // -------------------------------------------------------------
      // E. Playful Cursor Animation: Spring Halo + Velocity Liquid Ribbon
      // -------------------------------------------------------------
      if (hasMoved) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';

        // 1. Ambient Cursor Spotlight
        const spotRadius = 340;
        const spotGrad = ctx.createRadialGradient(
          mouseX,
          mouseY,
          0,
          mouseX,
          mouseY,
          spotRadius
        );
        spotGrad.addColorStop(0, 'rgba(255, 255, 255, 0.22)');
        spotGrad.addColorStop(0.25, 'rgba(192, 132, 252, 0.15)');
        spotGrad.addColorStop(0.6, 'rgba(124, 58, 237, 0.05)');
        spotGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.fillStyle = spotGrad;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, spotRadius, 0, Math.PI * 2);
        ctx.fill();

        // 2. Elastic Spring-Follower Liquid Ring (stretches with velocity!)
        const velAngle = Math.atan2(chaserVY, chaserVX);
        const velMag = Math.min(28, Math.hypot(chaserVX, chaserVY));
        const stretchX = 20 + velMag * 0.65;
        const stretchY = Math.max(10, 20 - velMag * 0.25);

        ctx.strokeStyle = 'rgba(216, 180, 254, 0.55)';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.ellipse(chaserX, chaserY, stretchX, stretchY, velAngle, 0, Math.PI * 2);
        ctx.stroke();

        // Crisp white center dot on cursor
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, 3, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }

      // 3. Dynamic Velocity-Width Tapered Liquid Ribbon Trail
      const now = performance.now();
      for (let i = trail.length - 1; i >= 0; i--) {
        const pt = trail[i];
        // Slight organic float on trail points
        pt.x += pt.vx * 0.08;
        pt.y += pt.vy * 0.08;
        const age = now - pt.time;
        pt.alpha = Math.max(0, 1 - age / 440);
        if (pt.alpha <= 0) {
          trail.splice(i, 1);
        }
      }

      if (trail.length > 2) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        for (let i = 1; i < trail.length - 1; i++) {
          const p0 = trail[i - 1];
          const p1 = trail[i];
          const p2 = trail[i + 1];

          const xc = (p1.x + p2.x) / 2;
          const yc = (p1.y + p2.y) / 2;
          const prevXc = (p0.x + p1.x) / 2;
          const prevYc = (p0.y + p1.y) / 2;

          const progress = i / trail.length;
          const dynamicWidth = (1 + p1.speed * 0.28) * progress;

          // Outer Purple Glow Ribbon
          ctx.beginPath();
          ctx.moveTo(prevXc, prevYc);
          ctx.quadraticCurveTo(p1.x, p1.y, xc, yc);
          ctx.strokeStyle = `rgba(168, 85, 247, ${p1.alpha * 0.28})`;
          ctx.lineWidth = dynamicWidth * 2.6;
          ctx.stroke();

          // Mid Lavender Core
          ctx.beginPath();
          ctx.moveTo(prevXc, prevYc);
          ctx.quadraticCurveTo(p1.x, p1.y, xc, yc);
          ctx.strokeStyle = `rgba(216, 180, 254, ${p1.alpha * 0.55})`;
          ctx.lineWidth = dynamicWidth * 0.9;
          ctx.stroke();

          // Hot White Center Thread
          ctx.beginPath();
          ctx.moveTo(prevXc, prevYc);
          ctx.quadraticCurveTo(p1.x, p1.y, xc, yc);
          ctx.strokeStyle = `rgba(255, 255, 255, ${p1.alpha * 0.95})`;
          ctx.lineWidth = Math.max(1, dynamicWidth * 0.28);
          ctx.stroke();
        }
        ctx.restore();
      }

      // -------------------------------------------------------------
      // F. Swirling Vortex Sparks Dissolve
      // -------------------------------------------------------------
      if (sparks.length > 0) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        for (let i = sparks.length - 1; i >= 0; i--) {
          const sp = sparks[i];
          // Curl/vortex rotation on velocity vector
          const cosS = Math.cos(sp.swirl);
          const sinS = Math.sin(sp.swirl);
          const nvx = sp.vx * cosS - sp.vy * sinS;
          const nvy = sp.vx * sinS + sp.vy * cosS;
          sp.vx = nvx * 0.96;
          sp.vy = nvy * 0.96 - 0.03;

          sp.x += sp.vx;
          sp.y += sp.vy;
          sp.life++;
          sp.alpha = Math.max(0, 1 - sp.life / sp.maxLife);

          if (sp.alpha <= 0) {
            sparks.splice(i, 1);
            continue;
          }

          if (sp.hue === 'purple') {
            ctx.fillStyle = `rgba(192, 132, 252, ${sp.alpha * 0.9})`;
          } else if (sp.hue === 'violet') {
            ctx.fillStyle = `rgba(147, 51, 234, ${sp.alpha * 0.9})`;
          } else {
            ctx.fillStyle = `rgba(255, 255, 255, ${sp.alpha * 0.95})`;
          }

          ctx.beginPath();
          ctx.arc(sp.x, sp.y, sp.size * sp.alpha + 0.4, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    const handleVisibilityChange = () => {
      if (document.hidden) {
        cancelAnimationFrame(animationFrameId);
      } else {
        animationFrameId = requestAnimationFrame(render);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ width: '100vw', height: '100vh' }}
    />
  );
};

import React, { useEffect, useRef } from 'react';

interface TrailPoint {
  x: number;
  y: number;
  time: number;
  alpha: number;
}

interface StardustSpark {
  x: number;
  y: number;
  vx: number;
  vy: number;
  alpha: number;
  life: number;
  maxLife: number;
  size: number;
  hue: 'purple' | 'white' | 'violet';
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

interface LiquidOrb3D {
  x: number;
  y: number;
  z: number;
  radius: number;
  colorInner: string;
  colorOuter: string;
  speed: number;
  phase: number;
}

interface AmbientDust {
  x: number;
  y: number;
  z: number;
  size: number;
  alpha: number;
  pulseSpeed: number;
  isPurple: boolean;
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

    let mouseX = width / 2;
    let mouseY = height / 3;
    let targetMouseX = mouseX;
    let targetMouseY = mouseY;
    let lastEventX = mouseX;
    let lastEventY = mouseY;
    let hasMoved = false;

    const trail: TrailPoint[] = [];
    const maxTrailLength = 42;
    const sparks: StardustSpark[] = [];

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const handlePointerMove = (e: PointerEvent) => {
      targetMouseX = e.clientX;
      targetMouseY = e.clientY;
      hasMoved = true;

      const now = performance.now();
      trail.push({
        x: e.clientX,
        y: e.clientY,
        time: now,
        alpha: 1.0
      });

      if (trail.length > maxTrailLength) {
        trail.shift();
      }

      const dist = Math.hypot(e.clientX - lastEventX, e.clientY - lastEventY);
      if (dist > 7 && sparks.length < 65) {
        const count = Math.min(3, Math.floor(dist / 10));
        const hues: Array<'purple' | 'white' | 'violet'> = ['purple', 'white', 'violet'];
        for (let i = 0; i < count; i++) {
          const angle = Math.random() * Math.PI * 2;
          const speed = Math.random() * 1.4 + 0.3;
          sparks.push({
            x: e.clientX + (Math.random() - 0.5) * 12,
            y: e.clientY + (Math.random() - 0.5) * 12,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed - 0.25,
            alpha: 0.95,
            life: 0,
            maxLife: Math.random() * 28 + 20,
            size: Math.random() * 2.0 + 0.8,
            hue: hues[Math.floor(Math.random() * hues.length)]
          });
        }
      }
      lastEventX = e.clientX;
      lastEventY = e.clientY;
    };
    window.addEventListener('pointermove', handlePointerMove);

    // -----------------------------------------------------------------
    // 1. Floating 3D Liquid Glass Refractive Orbs
    // -----------------------------------------------------------------
    const liquidOrbs: LiquidOrb3D[] = [
      {
        x: -320,
        y: -140,
        z: 120,
        radius: 190,
        colorInner: 'rgba(192, 132, 252, 0.22)',
        colorOuter: 'rgba(124, 58, 237, 0)',
        speed: 0.7,
        phase: 0
      },
      {
        x: 340,
        y: -60,
        z: 180,
        radius: 220,
        colorInner: 'rgba(168, 85, 247, 0.18)',
        colorOuter: 'rgba(88, 28, 135, 0)',
        speed: 0.55,
        phase: 2.1
      },
      {
        x: 0,
        y: -200,
        z: 80,
        radius: 160,
        colorInner: 'rgba(255, 255, 255, 0.14)',
        colorOuter: 'rgba(168, 85, 247, 0)',
        speed: 0.85,
        phase: 4.2
      }
    ];

    // -----------------------------------------------------------------
    // 2. 3D Ambient Dust Particles
    // -----------------------------------------------------------------
    const ambientDust: AmbientDust[] = [];
    for (let i = 0; i < 60; i++) {
      ambientDust.push({
        x: (Math.random() - 0.5) * 1800,
        y: (Math.random() - 0.5) * 1200,
        z: Math.random() * 650 - 120,
        size: Math.random() * 2.4 + 0.7,
        alpha: Math.random() * 0.45 + 0.12,
        pulseSpeed: Math.random() * 0.025 + 0.006,
        isPurple: Math.random() > 0.38
      });
    }

    // -----------------------------------------------------------------
    // 3. 3D Volumetric Multi-Faceted Crown Crystal & Icosahedron Meshes
    // -----------------------------------------------------------------
    const createCrownCrystal = (radius: number, heightScale: number) => {
      const vertices: Point3D[] = [];
      const faces: Face3D[] = [];
      const segments = 8;

      // 0: Top crown apex, 1: Bottom pavilion apex
      vertices.push({ x: 0, y: -radius * heightScale, z: 0 });
      vertices.push({ x: 0, y: radius * heightScale, z: 0 });

      // Upper girdle ring (indices 2..9)
      for (let i = 0; i < segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        vertices.push({
          x: Math.cos(theta) * radius,
          y: -radius * 0.28,
          z: Math.sin(theta) * radius
        });
      }

      // Lower girdle ring rotated by half-step (indices 10..17)
      for (let i = 0; i < segments; i++) {
        const theta = ((i + 0.5) / segments) * Math.PI * 2;
        vertices.push({
          x: Math.cos(theta) * radius * 0.88,
          y: radius * 0.28,
          z: Math.sin(theta) * radius * 0.88
        });
      }

      const tints: Array<'purple' | 'white' | 'violet'> = ['purple', 'white', 'violet'];

      for (let i = 0; i < segments; i++) {
        const next = (i + 1) % segments;
        const u0 = 2 + i;
        const u1 = 2 + next;
        const l0 = 10 + i;
        const l1 = 10 + ((i + segments - 1) % segments);

        // Top crown facets
        faces.push({
          indices: [0, u0, u1],
          tint: tints[i % 3],
          baseAlpha: 0.065
        });

        // Middle girdle facets (2 triangles per segment)
        faces.push({
          indices: [u0, l0, u1],
          tint: tints[(i + 1) % 3],
          baseAlpha: 0.08
        });
        faces.push({
          indices: [u0, l1, l0],
          tint: tints[(i + 2) % 3],
          baseAlpha: 0.07
        });

        // Bottom pavilion facets
        faces.push({
          indices: [1, l0, l1],
          tint: tints[i % 3],
          baseAlpha: 0.06
        });
      }

      return { vertices, faces };
    };

    const mainCrystal = createCrownCrystal(115, 1.35);
    const rightCrystal = createCrownCrystal(72, 1.45);
    const leftCrystal = createCrownCrystal(68, 1.5);

    // -----------------------------------------------------------------
    // 4. 3D Orbiting Glass Ring Around Center Crystal
    // -----------------------------------------------------------------
    const ringPoints: Point3D[] = [];
    const ringSegments = 36;
    for (let i = 0; i < ringSegments; i++) {
      const angle = (i / ringSegments) * Math.PI * 2;
      ringPoints.push({
        x: Math.cos(angle) * 210,
        y: Math.sin(angle) * 28,
        z: Math.sin(angle) * 210
      });
    }

    let rotX = 0.25;
    let rotY = 0;
    let rotZ = 0.1;
    let timeTick = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      mouseX += (targetMouseX - mouseX) * 0.12;
      mouseY += (targetMouseY - mouseY) * 0.12;

      const parallaxX = (mouseX - width / 2) * 0.065;
      const parallaxY = (mouseY - height / 2) * 0.065;

      if (!prefersReducedMotion) {
        rotX += 0.0028;
        rotY += 0.0052;
        rotZ += 0.0018;
        timeTick += 0.02;
      }

      // -------------------------------------------------------------
      // A. Render 3D Floating Refractive Liquid Orbs
      // -------------------------------------------------------------
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      for (const orb of liquidOrbs) {
        const floatX = orb.x + Math.sin(timeTick * orb.speed + orb.phase) * 45;
        const floatY = orb.y + Math.cos(timeTick * orb.speed * 0.8 + orb.phase) * 30;
        const fov = 450;
        const scale = fov / (fov + orb.z);
        const sx = width / 2 + (floatX + parallaxX * 1.1) * scale;
        const sy = height * 0.42 + (floatY + parallaxY * 1.1) * scale;
        const r = orb.radius * scale;

        const grad = ctx.createRadialGradient(sx - r * 0.25, sy - r * 0.25, r * 0.05, sx, sy, r);
        grad.addColorStop(0, 'rgba(255, 255, 255, 0.22)');
        grad.addColorStop(0.35, orb.colorInner);
        grad.addColorStop(1, orb.colorOuter);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(sx, sy, r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();

      // -------------------------------------------------------------
      // B. Render 3D Ambient Dust Field (Purple & White Depth Layers)
      // -------------------------------------------------------------
      ctx.save();
      for (const dust of ambientDust) {
        const fov = 420;
        const pz = dust.z + parallaxY * 0.3;
        const scale = fov / (fov + pz);
        if (scale <= 0) continue;

        const px = width / 2 + (dust.x + parallaxX * 0.55) * scale;
        const py = height / 2 + (dust.y + parallaxY * 0.55) * scale;

        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          const pulse = (Math.sin(timeTick * dust.pulseSpeed * 22) + 1) * 0.5;
          const currentAlpha = dust.alpha * (0.55 + pulse * 0.45) * Math.min(1, scale);

          ctx.fillStyle = dust.isPurple
            ? `rgba(192, 132, 252, ${currentAlpha})`
            : `rgba(255, 255, 255, ${currentAlpha})`;
          ctx.beginPath();
          ctx.arc(px, py, dust.size * scale, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.restore();

      // -------------------------------------------------------------
      // C. Render 3D Undulating Sine-Wave Perspective Floor Grid
      // -------------------------------------------------------------
      const horizonY = height * 0.67 + parallaxY * 0.32;
      ctx.save();
      const cols = 18;
      const rows = 10;

      // Longitudinal perspective rays with wave distortion
      for (let c = -cols; c <= cols; c++) {
        const normalizedC = c / cols;
        ctx.beginPath();
        for (let r = 0; r <= rows; r++) {
          const t = r / rows;
          const depthFactor = Math.pow(t, 2.1);
          const spread = width * 1.45;
          const xBase = width / 2 + parallaxX * 0.8 + normalizedC * spread * depthFactor;
          const waveY =
            Math.sin(normalizedC * 5 + timeTick * 1.3 + t * 4) * 12 * depthFactor;
          const yPos = horizonY + depthFactor * (height - horizonY) + waveY;

          if (r === 0) ctx.moveTo(xBase, yPos);
          else ctx.lineTo(xBase, yPos);
        }
        const grad = ctx.createLinearGradient(0, horizonY, 0, height);
        grad.addColorStop(0, 'rgba(168, 85, 247, 0)');
        grad.addColorStop(0.45, 'rgba(168, 85, 247, 0.08)');
        grad.addColorStop(1, 'rgba(255, 255, 255, 0.12)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Transverse wave lines
      for (let r = 1; r <= rows; r++) {
        const t = r / rows;
        const depthFactor = Math.pow(t, 2.1);
        ctx.beginPath();
        for (let c = -cols; c <= cols; c++) {
          const normalizedC = c / cols;
          const spread = width * 1.45;
          const xPos = width / 2 + parallaxX * 0.8 + normalizedC * spread * depthFactor;
          const waveY =
            Math.sin(normalizedC * 5 + timeTick * 1.3 + t * 4) * 12 * depthFactor;
          const yPos = horizonY + depthFactor * (height - horizonY) + waveY;

          if (c === -cols) ctx.moveTo(xPos, yPos);
          else ctx.lineTo(xPos, yPos);
        }
        const alpha = depthFactor * 0.14;
        ctx.strokeStyle =
          r % 2 === 0
            ? `rgba(192, 132, 252, ${alpha})`
            : `rgba(255, 255, 255, ${alpha * 0.75})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      ctx.restore();

      // -------------------------------------------------------------
      // D. Render Z-Sorted Volumetric 3D Liquid Glass Crystals
      // -------------------------------------------------------------
      const renderZSortedCrystal = (
        mesh: { vertices: Point3D[]; faces: Face3D[] },
        cx: number,
        cy: number,
        rX: number,
        rY: number,
        rZ: number,
        scale: number
      ) => {
        const fov = 460;

        // Ambient halo behind each crystal
        ctx.save();
        const haloGrad = ctx.createRadialGradient(cx, cy, 5, cx, cy, 150 * scale);
        haloGrad.addColorStop(0, 'rgba(168, 85, 247, 0.22)');
        haloGrad.addColorStop(0.5, 'rgba(124, 58, 237, 0.06)');
        haloGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = haloGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, 150 * scale, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        const transformed = mesh.vertices.map(v => {
          const y1 = v.y * Math.cos(rX) - v.z * Math.sin(rX);
          const z1 = v.y * Math.sin(rX) + v.z * Math.cos(rX);
          const x2 = v.x * Math.cos(rY) + z1 * Math.sin(rY);
          const z2 = -v.x * Math.sin(rY) + z1 * Math.cos(rY);
          const x3 = x2 * Math.cos(rZ) - y1 * Math.sin(rZ);
          const y3 = x2 * Math.sin(rZ) + y1 * Math.cos(rZ);

          const dist = fov / (fov + z2 + 240);
          return {
            x: cx + x3 * dist * scale,
            y: cy + y3 * dist * scale,
            z: z2,
            rawX: x3,
            rawY: y3,
            rawZ: z2
          };
        });

        const lx = mouseX - cx;
        const ly = mouseY - cy;
        const lz = -280;
        const lLen = Math.hypot(lx, ly, lz) || 1;
        const normLX = lx / lLen;
        const normLY = ly / lLen;
        const normLZ = lz / lLen;

        // Painter's Algorithm: Sort faces from back (highest Z) to front (lowest Z)
        const sortedFaces = mesh.faces
          .map(face => {
            const v0 = transformed[face.indices[0]];
            const v1 = transformed[face.indices[1]];
            const v2 = transformed[face.indices[2]];
            const avgZ = (v0.z + v1.z + v2.z) / 3;
            return { face, v0, v1, v2, avgZ };
          })
          .sort((a, b) => b.avgZ - a.avgZ);

        ctx.save();
        for (const item of sortedFaces) {
          const { face, v0, v1, v2 } = item;

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
            ? face.baseAlpha + specular * 0.34 + dot * 0.1
            : face.baseAlpha * 0.35;
          const strokeAlpha = isFront ? 0.24 + specular * 0.45 : 0.07;

          if (face.tint === 'purple') {
            ctx.fillStyle = `rgba(168, 85, 247, ${fillAlpha})`;
            ctx.strokeStyle = `rgba(216, 180, 254, ${strokeAlpha})`;
          } else if (face.tint === 'violet') {
            ctx.fillStyle = `rgba(124, 58, 237, ${fillAlpha})`;
            ctx.strokeStyle = `rgba(192, 132, 252, ${strokeAlpha})`;
          } else {
            ctx.fillStyle = `rgba(255, 255, 255, ${fillAlpha * 0.9})`;
            ctx.strokeStyle = `rgba(255, 255, 255, ${strokeAlpha})`;
          }

          ctx.lineWidth = isFront ? 1.25 : 0.65;

          ctx.beginPath();
          ctx.moveTo(v0.x, v0.y);
          ctx.lineTo(v1.x, v1.y);
          ctx.lineTo(v2.x, v2.y);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }

        // Specular vertex stars on front-most vertices
        for (const pt of transformed) {
          if (pt.z < 0) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 1.5, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        ctx.restore();
      };

      // Center Crown Crystal + Orbiting Ring
      const centerCx = width / 2 + parallaxX * 1.45;
      const centerCy = height * 0.28 + parallaxY * 1.45;

      renderZSortedCrystal(
        mainCrystal,
        centerCx,
        centerCy,
        rotX,
        rotY,
        rotZ,
        1.18
      );

      // Render 3D Orbital Glass Ring around Center Crystal
      ctx.save();
      ctx.beginPath();
      for (let i = 0; i <= ringPoints.length; i++) {
        const pt = ringPoints[i % ringPoints.length];
        const rX = rotX * 0.7 + 0.5;
        const rY = -rotY * 1.1;
        const y1 = pt.y * Math.cos(rX) - pt.z * Math.sin(rX);
        const z1 = pt.y * Math.sin(rX) + pt.z * Math.cos(rX);
        const x2 = pt.x * Math.cos(rY) + z1 * Math.sin(rY);
        const z2 = -pt.x * Math.sin(rY) + z1 * Math.cos(rY);

        const dist = 460 / (460 + z2 + 240);
        const sx = centerCx + x2 * dist * 1.2;
        const sy = centerCy + y1 * dist * 1.2;

        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      }
      ctx.strokeStyle = 'rgba(216, 180, 254, 0.28)';
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.restore();

      // Right Floating Crystal
      renderZSortedCrystal(
        rightCrystal,
        width * 0.85 + parallaxX * 0.85,
        height * 0.42 + parallaxY * 0.85 + Math.sin(timeTick * 1.2) * 12,
        -rotX * 0.9,
        -rotY * 0.85,
        rotZ * 0.7,
        1.05
      );

      // Left Floating Crystal
      renderZSortedCrystal(
        leftCrystal,
        width * 0.14 + parallaxX * 0.95,
        height * 0.56 + parallaxY * 0.95 + Math.cos(timeTick * 1.1) * 14,
        rotX * 0.8,
        -rotY * 0.75,
        -rotZ * 0.6,
        1.0
      );

      // -------------------------------------------------------------
      // E. Interactive Cursor Spotlight (Purple + White Liquid Radiance)
      // -------------------------------------------------------------
      if (hasMoved) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';

        const spotRadius = 380;
        const spotGrad = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, spotRadius);
        spotGrad.addColorStop(0, 'rgba(255, 255, 255, 0.2)');
        spotGrad.addColorStop(0.22, 'rgba(192, 132, 252, 0.14)');
        spotGrad.addColorStop(0.55, 'rgba(124, 58, 237, 0.05)');
        spotGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.fillStyle = spotGrad;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, spotRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // -------------------------------------------------------------
      // F. Silk-Smooth Catmull-Rom Spline Purple & White Light Trail
      // -------------------------------------------------------------
      const now = performance.now();
      for (let i = trail.length - 1; i >= 0; i--) {
        const pt = trail[i];
        const age = now - pt.time;
        pt.alpha = Math.max(0, 1 - age / 480);
        if (pt.alpha <= 0) {
          trail.splice(i, 1);
        }
      }

      if (trail.length > 2) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        const traceCurve = () => {
          ctx.beginPath();
          ctx.moveTo(trail[0].x, trail[0].y);
          for (let i = 1; i < trail.length - 1; i++) {
            const xc = (trail[i].x + trail[i + 1].x) / 2;
            const yc = (trail[i].y + trail[i + 1].y) / 2;
            ctx.quadraticCurveTo(trail[i].x, trail[i].y, xc, yc);
          }
        };

        // Outer Royal Purple Bloom
        traceCurve();
        ctx.strokeStyle = 'rgba(168, 85, 247, 0.22)';
        ctx.lineWidth = 20;
        ctx.stroke();

        // Mid Electric Lavender Thread
        traceCurve();
        ctx.strokeStyle = 'rgba(216, 180, 254, 0.5)';
        ctx.lineWidth = 5;
        ctx.stroke();

        // Pure White Hot Core
        traceCurve();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.lineWidth = 1.4;
        ctx.stroke();

        ctx.restore();
      }

      // -------------------------------------------------------------
      // G. Bi-Color Stardust Particle Dissolve
      // -------------------------------------------------------------
      if (sparks.length > 0) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        for (let i = sparks.length - 1; i >= 0; i--) {
          const sp = sparks[i];
          sp.x += sp.vx;
          sp.y += sp.vy;
          sp.vx *= 0.96;
          sp.vy *= 0.96;
          sp.life++;
          sp.alpha = Math.max(0, 1 - sp.life / sp.maxLife);

          if (sp.alpha <= 0) {
            sparks.splice(i, 1);
            continue;
          }

          if (sp.hue === 'purple') {
            ctx.fillStyle = `rgba(192, 132, 252, ${sp.alpha * 0.85})`;
          } else if (sp.hue === 'violet') {
            ctx.fillStyle = `rgba(147, 51, 234, ${sp.alpha * 0.85})`;
          } else {
            ctx.fillStyle = `rgba(255, 255, 255, ${sp.alpha * 0.85})`;
          }

          ctx.beginPath();
          ctx.arc(sp.x, sp.y, sp.size, 0, Math.PI * 2);
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

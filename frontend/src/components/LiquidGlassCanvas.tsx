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
}

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface Face3D {
  indices: number[];
  baseAlpha: number;
}

interface AmbientDust {
  x: number;
  y: number;
  z: number;
  size: number;
  alpha: number;
  pulseSpeed: number;
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

    // Mouse coordinates with smooth lerping
    let mouseX = width / 2;
    let mouseY = height / 3;
    let targetMouseX = mouseX;
    let targetMouseY = mouseY;
    let lastEventX = mouseX;
    let lastEventY = mouseY;
    let hasMoved = false;

    // Spline Trail buffer & Stardust queue
    const trail: TrailPoint[] = [];
    const maxTrailLength = 40;
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

      // Spawn subtle stardust particles on movement
      const dist = Math.hypot(e.clientX - lastEventX, e.clientY - lastEventY);
      if (dist > 8 && sparks.length < 50) {
        const count = Math.min(2, Math.floor(dist / 12));
        for (let i = 0; i < count; i++) {
          const angle = Math.random() * Math.PI * 2;
          const speed = Math.random() * 1.2 + 0.3;
          sparks.push({
            x: e.clientX + (Math.random() - 0.5) * 10,
            y: e.clientY + (Math.random() - 0.5) * 10,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed - 0.2,
            alpha: 0.9,
            life: 0,
            maxLife: Math.random() * 25 + 20,
            size: Math.random() * 1.8 + 0.8
          });
        }
      }
      lastEventX = e.clientX;
      lastEventY = e.clientY;
    };
    window.addEventListener('pointermove', handlePointerMove);

    // -----------------------------------------------------------------
    // 3D Ambient Dust Particles (Depth Layers)
    // -----------------------------------------------------------------
    const ambientDust: AmbientDust[] = [];
    for (let i = 0; i < 45; i++) {
      ambientDust.push({
        x: (Math.random() - 0.5) * 1600,
        y: (Math.random() - 0.5) * 1200,
        z: Math.random() * 600 - 100,
        size: Math.random() * 2.2 + 0.8,
        alpha: Math.random() * 0.4 + 0.1,
        pulseSpeed: Math.random() * 0.02 + 0.005
      });
    }

    // -----------------------------------------------------------------
    // 3D Volumetric Polyhedral Crystal Gems
    // -----------------------------------------------------------------
    // Gem 1: Large Faceted Diamond Bipyramid (Top-Center)
    const gemVertices1: Point3D[] = [
      { x: 0, y: -130, z: 0 },   // Top apex
      { x: 95, y: 0, z: -95 },   // Mid ring 1
      { x: -95, y: 0, z: -95 },  // Mid ring 2
      { x: -95, y: 0, z: 95 },   // Mid ring 3
      { x: 95, y: 0, z: 95 },    // Mid ring 4
      { x: 0, y: 130, z: 0 }     // Bottom apex
    ];
    const gemFaces1: Face3D[] = [
      // Top hemisphere
      { indices: [0, 1, 4], baseAlpha: 0.06 },
      { indices: [0, 4, 3], baseAlpha: 0.08 },
      { indices: [0, 3, 2], baseAlpha: 0.05 },
      { indices: [0, 2, 1], baseAlpha: 0.07 },
      // Bottom hemisphere
      { indices: [5, 4, 1], baseAlpha: 0.05 },
      { indices: [5, 3, 4], baseAlpha: 0.07 },
      { indices: [5, 2, 3], baseAlpha: 0.06 },
      { indices: [5, 1, 2], baseAlpha: 0.08 }
    ];

    // Gem 2: Precision Cut Crystal (Upper Right)
    const gemVertices2: Point3D[] = [
      { x: 0, y: -80, z: 0 },
      { x: 65, y: -15, z: -60 },
      { x: -65, y: -15, z: -60 },
      { x: -65, y: -15, z: 60 },
      { x: 65, y: -15, z: 60 },
      { x: 0, y: 85, z: 0 }
    ];

    // Gem 3: Floating Monolith Crystal (Lower Left)
    const gemVertices3: Point3D[] = [
      { x: 0, y: -90, z: 0 },
      { x: 50, y: 0, z: -45 },
      { x: -50, y: 0, z: -45 },
      { x: -45, y: 0, z: 50 },
      { x: 45, y: 0, z: 50 },
      { x: 0, y: 90, z: 0 }
    ];

    let rotX = 0;
    let rotY = 0;
    let rotZ = 0;
    let timeTick = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Smooth mouse interpolation
      mouseX += (targetMouseX - mouseX) * 0.14;
      mouseY += (targetMouseY - mouseY) * 0.14;

      const parallaxX = (mouseX - width / 2) * 0.06;
      const parallaxY = (mouseY - height / 2) * 0.06;

      if (!prefersReducedMotion) {
        rotX += 0.0035;
        rotY += 0.005;
        rotZ += 0.002;
        timeTick += 0.02;
      }

      // -------------------------------------------------------------
      // 1. Draw 3D Ambient Dust Field with Depth Parallax
      // -------------------------------------------------------------
      ctx.save();
      for (const dust of ambientDust) {
        const fov = 400;
        const pz = dust.z + parallaxY * 0.3;
        const scale = fov / (fov + pz);
        const px = width / 2 + (dust.x + parallaxX * 0.5) * scale;
        const py = height / 2 + (dust.y + parallaxY * 0.5) * scale;

        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          const pulse = (Math.sin(timeTick * dust.pulseSpeed * 20) + 1) * 0.5;
          const currentAlpha = dust.alpha * (0.6 + pulse * 0.4) * Math.min(1, scale);
          
          ctx.fillStyle = `rgba(255, 255, 255, ${currentAlpha})`;
          ctx.beginPath();
          ctx.arc(px, py, dust.size * scale, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.restore();

      // -------------------------------------------------------------
      // 2. Draw 3D Perspective Ground Grid (Infinite Plane)
      // -------------------------------------------------------------
      const horizonY = height * 0.68 + parallaxY * 0.35;
      ctx.save();
      const gridCount = 14;
      for (let i = -gridCount; i <= gridCount; i++) {
        const xOffset = i * (width / gridCount) + parallaxX * 0.7;
        const grad = ctx.createLinearGradient(width / 2 + parallaxX * 0.8, horizonY, xOffset, height);
        grad.addColorStop(0, 'rgba(255, 255, 255, 0)');
        grad.addColorStop(0.3, 'rgba(255, 255, 255, 0.015)');
        grad.addColorStop(1, 'rgba(255, 255, 255, 0.07)');

        ctx.strokeStyle = grad;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(width / 2 + parallaxX * 0.8, horizonY);
        ctx.lineTo(xOffset, height);
        ctx.stroke();
      }

      for (let z = 1; z <= 8; z++) {
        const lineY = horizonY + Math.pow(z / 8, 2.3) * (height - horizonY);
        const alpha = (z / 8) * 0.065;
        ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, lineY);
        ctx.lineTo(width, lineY);
        ctx.stroke();
      }
      ctx.restore();

      // -------------------------------------------------------------
      // 3. Render Volumetric 3D Glass Crystals with Normal-Vector Lighting
      // -------------------------------------------------------------
      const renderVolumetricGem = (
        vertices: Point3D[],
        faces: Face3D[],
        cx: number,
        cy: number,
        rX: number,
        rY: number,
        rZ: number,
        scale: number
      ) => {
        const fov = 420;

        // Transform vertices into 3D world space
        const transformed = vertices.map(v => {
          // X rotation
          let y1 = v.y * Math.cos(rX) - v.z * Math.sin(rX);
          let z1 = v.y * Math.sin(rX) + v.z * Math.cos(rX);
          // Y rotation
          let x2 = v.x * Math.cos(rY) + z1 * Math.sin(rY);
          let z2 = -v.x * Math.sin(rY) + z1 * Math.cos(rY);
          // Z rotation
          let x3 = x2 * Math.cos(rZ) - y1 * Math.sin(rZ);
          let y3 = x2 * Math.sin(rZ) + y1 * Math.cos(rZ);

          const dist = fov / (fov + z2 + 200);
          return {
            x: cx + x3 * dist * scale,
            y: cy + y3 * dist * scale,
            z: z2,
            rawX: x3,
            rawY: y3,
            rawZ: z2
          };
        });

        // Light vector from cursor position to crystal center
        const lx = mouseX - cx;
        const ly = mouseY - cy;
        const lz = -250;
        const lLen = Math.hypot(lx, ly, lz) || 1;
        const normLX = lx / lLen;
        const normLY = ly / lLen;
        const normLZ = lz / lLen;

        ctx.save();
        for (const face of faces) {
          const v0 = transformed[face.indices[0]];
          const v1 = transformed[face.indices[1]];
          const v2 = transformed[face.indices[2]];

          // Surface Normal calculation (cross product of edges)
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

          // Diffuse light dot product
          const dot = Math.max(0, nx * normLX + ny * normLY + nz * normLZ);
          // Specular shine power
          const specular = Math.pow(dot, 3);

          const isFront = nz < 0;
          const fillAlpha = isFront
            ? face.baseAlpha + specular * 0.28 + dot * 0.08
            : face.baseAlpha * 0.4;
          const strokeAlpha = isFront
            ? 0.22 + specular * 0.35
            : 0.06;

          ctx.fillStyle = `rgba(255, 255, 255, ${fillAlpha})`;
          ctx.strokeStyle = `rgba(255, 255, 255, ${strokeAlpha})`;
          ctx.lineWidth = isFront ? 1.4 : 0.8;

          ctx.beginPath();
          ctx.moveTo(v0.x, v0.y);
          ctx.lineTo(v1.x, v1.y);
          ctx.lineTo(v2.x, v2.y);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }

        // Vertex specular gleams
        for (const pt of transformed) {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 1.6, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      };

      // Render Gem 1: Large Center-Top Crystal
      renderVolumetricGem(
        gemVertices1,
        gemFaces1,
        width / 2 + parallaxX * 1.5,
        height * 0.26 + parallaxY * 1.5,
        rotX,
        rotY,
        rotZ,
        1.35
      );

      // Render Gem 2: Upper Right Facet
      renderVolumetricGem(
        gemVertices2,
        gemFaces1,
        width * 0.84 + parallaxX * 0.8,
        height * 0.44 + parallaxY * 0.8,
        -rotX * 0.9,
        -rotY * 0.8,
        rotZ * 0.6,
        1.1
      );

      // Render Gem 3: Lower Left Monolith
      renderVolumetricGem(
        gemVertices3,
        gemFaces1,
        width * 0.14 + parallaxX * 0.9,
        height * 0.58 + parallaxY * 0.9,
        rotX * 0.8,
        -rotY * 0.7,
        -rotZ * 0.5,
        1.05
      );

      // -------------------------------------------------------------
      // 4. Interactive Cursor Spotlight (Ambient Liquid Radiance)
      // -------------------------------------------------------------
      if (hasMoved) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';

        const spotRadius = 340;
        const spotGrad = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, spotRadius);
        spotGrad.addColorStop(0, 'rgba(255, 255, 255, 0.22)');
        spotGrad.addColorStop(0.2, 'rgba(255, 255, 255, 0.09)');
        spotGrad.addColorStop(0.55, 'rgba(255, 255, 255, 0.025)');
        spotGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');

        ctx.fillStyle = spotGrad;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, spotRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // -------------------------------------------------------------
      // 5. Silk-Smooth Catmull-Rom Spline Liquid Light Trail
      // -------------------------------------------------------------
      const now = performance.now();
      for (let i = trail.length - 1; i >= 0; i--) {
        const pt = trail[i];
        const age = now - pt.time;
        // Fade smoothly over 480ms
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

        // Outer Ethereal Liquid Sheen (Thick Diffuse Beam)
        ctx.beginPath();
        ctx.moveTo(trail[0].x, trail[0].y);
        for (let i = 1; i < trail.length - 1; i++) {
          const xc = (trail[i].x + trail[i + 1].x) / 2;
          const yc = (trail[i].y + trail[i + 1].y) / 2;
          ctx.quadraticCurveTo(trail[i].x, trail[i].y, xc, yc);
        }
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 16;
        ctx.stroke();

        // Focused Liquid Core (Sharp Luminous Thread)
        ctx.beginPath();
        ctx.moveTo(trail[0].x, trail[0].y);
        for (let i = 1; i < trail.length - 1; i++) {
          const xc = (trail[i].x + trail[i + 1].x) / 2;
          const yc = (trail[i].y + trail[i + 1].y) / 2;
          ctx.quadraticCurveTo(trail[i].x, trail[i].y, xc, yc);
        }
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
        ctx.lineWidth = 4;
        ctx.stroke();

        // Intense White Centerline
        ctx.beginPath();
        ctx.moveTo(trail[0].x, trail[0].y);
        for (let i = 1; i < trail.length - 1; i++) {
          const xc = (trail[i].x + trail[i + 1].x) / 2;
          const yc = (trail[i].y + trail[i + 1].y) / 2;
          ctx.quadraticCurveTo(trail[i].x, trail[i].y, xc, yc);
        }
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 1.2;
        ctx.stroke();

        ctx.restore();
      }

      // -------------------------------------------------------------
      // 6. Stardust Particle Dissolve
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

          ctx.fillStyle = `rgba(255, 255, 255, ${sp.alpha * 0.7})`;
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

import React, { useEffect, useRef } from 'react';

interface TrailPoint {
  x: number;
  y: number;
  alpha: number;
  time: number;
}

interface Point3D {
  x: number;
  y: number;
  z: number;
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

    // Mouse coordinates & lerped parallax
    let mouseX = width / 2;
    let mouseY = height / 3;
    let targetMouseX = mouseX;
    let targetMouseY = mouseY;
    let hasMoved = false;

    // Light trail queue
    const trail: TrailPoint[] = [];
    const maxTrailLength = 32;

    // Reduced motion preference check
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Resize handler
    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Pointer move handler
    const handlePointerMove = (e: PointerEvent) => {
      targetMouseX = e.clientX;
      targetMouseY = e.clientY;
      hasMoved = true;

      // Add to light trail
      const now = performance.now();
      trail.push({
        x: e.clientX,
        y: e.clientY,
        alpha: 1.0,
        time: now
      });

      if (trail.length > maxTrailLength) {
        trail.shift();
      }
    };
    window.addEventListener('pointermove', handlePointerMove);

    // 3D Polyhedron Geometries (Octahedron / Icosahedron-style facets)
    // Shape 1: Top-Center Floating Crystal (Vanishing behind dropzone)
    const vertices1: Point3D[] = [
      { x: 0, y: -120, z: 0 },
      { x: 90, y: 0, z: -90 },
      { x: -90, y: 0, z: -90 },
      { x: -90, y: 0, z: 90 },
      { x: 90, y: 0, z: 90 },
      { x: 0, y: 120, z: 0 },
    ];
    const edges1 = [
      [0, 1], [0, 2], [0, 3], [0, 4],
      [1, 2], [2, 3], [3, 4], [4, 1],
      [5, 1], [5, 2], [5, 3], [5, 4]
    ];

    // Shape 2: Right Ambient Geode
    const vertices2: Point3D[] = [
      { x: 0, y: -70, z: 0 },
      { x: 60, y: 0, z: -50 },
      { x: -60, y: 0, z: -50 },
      { x: -50, y: 0, z: 60 },
      { x: 50, y: 0, z: 60 },
      { x: 0, y: 70, z: 0 },
    ];

    let rotX = 0;
    let rotY = 0;
    let rotZ = 0;

    // Main animation loop
    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Smooth mouse interpolation
      mouseX += (targetMouseX - mouseX) * 0.12;
      mouseY += (targetMouseY - mouseY) * 0.12;

      const parallaxX = (mouseX - width / 2) * 0.05;
      const parallaxY = (mouseY - height / 2) * 0.05;

      if (!prefersReducedMotion) {
        rotX += 0.004;
        rotY += 0.006;
        rotZ += 0.002;
      }

      // -------------------------------------------------------------
      // 1. Draw 3D Perspective Ground Grid
      // -------------------------------------------------------------
      const horizonY = height * 0.65 + parallaxY * 0.4;
      const fov = 420;
      ctx.save();
      ctx.lineWidth = 1;

      // Draw converging perspective lines
      const gridLines = 14;
      for (let i = -gridLines; i <= gridLines; i++) {
        const xOffset = i * (width / gridLines) + parallaxX * 0.6;
        const grad = ctx.createLinearGradient(width / 2 + parallaxX, horizonY, xOffset, height);
        grad.addColorStop(0, 'rgba(255, 255, 255, 0)');
        grad.addColorStop(0.3, 'rgba(255, 255, 255, 0.02)');
        grad.addColorStop(1, 'rgba(255, 255, 255, 0.08)');

        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(width / 2 + parallaxX, horizonY);
        ctx.lineTo(xOffset, height);
        ctx.stroke();
      }

      // Draw horizontal cross grid lines with perspective spacing
      for (let z = 1; z <= 7; z++) {
        const lineY = horizonY + Math.pow(z / 7, 2.2) * (height - horizonY);
        const alpha = (z / 7) * 0.07;
        ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.beginPath();
        ctx.moveTo(0, lineY);
        ctx.lineTo(width, lineY);
        ctx.stroke();
      }
      ctx.restore();

      // -------------------------------------------------------------
      // 2. Draw Floating 3D Geometric Facets (Liquid Glass Wireframes)
      // -------------------------------------------------------------
      const project = (p: Point3D, cx: number, cy: number, rX: number, rY: number, rZ: number, scaleFactor: number) => {
        // Rotate around X
        let y1 = p.y * Math.cos(rX) - p.z * Math.sin(rX);
        let z1 = p.y * Math.sin(rX) + p.z * Math.cos(rX);

        // Rotate around Y
        let x2 = p.x * Math.cos(rY) + z1 * Math.sin(rY);
        let z2 = -p.x * Math.sin(rY) + z1 * Math.cos(rY);

        // Rotate around Z
        let x3 = x2 * Math.cos(rZ) - y1 * Math.sin(rZ);
        let y3 = x2 * Math.sin(rZ) + y1 * Math.cos(rZ);

        const dist = fov / (fov + z2 + 180);
        return {
          x: cx + x3 * dist * scaleFactor,
          y: cy + y3 * dist * scaleFactor,
          z: z2,
          scale: dist
        };
      };

      // Draw Shape 1: Top Center floating facet
      const center1X = width / 2 + parallaxX * 1.5;
      const center1Y = height * 0.28 + parallaxY * 1.5;
      const proj1 = vertices1.map(v => project(v, center1X, center1Y, rotX, rotY, rotZ, 1.4));

      ctx.save();
      for (const [startIdx, endIdx] of edges1) {
        const p1 = proj1[startIdx];
        const p2 = proj1[endIdx];
        const avgZ = (p1.z + p2.z) / 2;
        const edgeAlpha = Math.max(0.04, Math.min(0.24, 0.15 + avgZ * 0.001));

        ctx.strokeStyle = `rgba(255, 255, 255, ${edgeAlpha})`;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }

      // Subtle vertex gleams
      for (const p of proj1) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();

      // Draw Shape 2: Upper Right Facet
      const center2X = width * 0.82 + parallaxX * 0.8;
      const center2Y = height * 0.45 + parallaxY * 0.8;
      const proj2 = vertices2.map(v => project(v, center2X, center2Y, -rotX * 0.8, -rotY * 0.9, rotZ * 0.5, 1.1));

      ctx.save();
      for (const [startIdx, endIdx] of edges1) {
        const p1 = proj2[startIdx];
        const p2 = proj2[endIdx];
        const avgZ = (p1.z + p2.z) / 2;
        const edgeAlpha = Math.max(0.03, Math.min(0.18, 0.1 + avgZ * 0.001));

        ctx.strokeStyle = `rgba(255, 255, 255, ${edgeAlpha})`;
        ctx.lineWidth = 1.0;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }
      ctx.restore();

      // -------------------------------------------------------------
      // 3. Interactive Cursor Spotlight (Liquid Light Diffuser)
      // -------------------------------------------------------------
      if (hasMoved) {
        const spotlightRadius = 320;
        const spotGrad = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, spotlightRadius);
        spotGrad.addColorStop(0, 'rgba(255, 255, 255, 0.18)');
        spotGrad.addColorStop(0.25, 'rgba(255, 255, 255, 0.07)');
        spotGrad.addColorStop(0.65, 'rgba(255, 255, 255, 0.02)');
        spotGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');

        ctx.fillStyle = spotGrad;
        ctx.beginPath();
        ctx.arc(mouseX, mouseY, spotlightRadius, 0, Math.PI * 2);
        ctx.fill();
      }

      // -------------------------------------------------------------
      // 4. Interactive Cursor Light Trail (Fading Luminous Ribbon)
      // -------------------------------------------------------------
      const now = performance.now();
      for (let i = trail.length - 1; i >= 0; i--) {
        const p = trail[i];
        const age = now - p.time;
        // Fade over 450ms
        p.alpha = Math.max(0, 1 - age / 450);

        if (p.alpha <= 0) {
          trail.splice(i, 1);
        }
      }

      if (trail.length > 2) {
        ctx.save();
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        for (let i = 1; i < trail.length; i++) {
          const p1 = trail[i - 1];
          const p2 = trail[i];
          const avgAlpha = ((p1.alpha + p2.alpha) / 2) * 0.45;

          if (avgAlpha > 0.01) {
            // Glowing outer beam
            ctx.strokeStyle = `rgba(255, 255, 255, ${avgAlpha * 0.4})`;
            ctx.lineWidth = (i / trail.length) * 14 + 4;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            // Intense inner white core
            ctx.strokeStyle = `rgba(255, 255, 255, ${avgAlpha * 0.9})`;
            ctx.lineWidth = (i / trail.length) * 3 + 1;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    // Pause rendering when tab is hidden
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

# VisionOS / iOS 18+ Liquid Glass & Volumetric 3D Engine Design

**Date:** 2026-11-11  
**Author:** oynu & Antigravity (Google DeepMind)  
**Status:** Approved

---

## 1. Intent & Purpose

Elevate Viddy's visual fidelity to top-tier Apple VisionOS / iOS 18+ standards:
1. **Silk-Smooth Liquid Light Trail**: Seamless Catmull-Rom spline curves with additive blending (`screen`/`lighter`), smooth width tapering, and micro-luminance stardust.
2. **Volumetric 3D Glass Geometry**: 3D faceted gems with semi-transparent shaded polygon faces calculated via 3D normal vectors relative to cursor light, paired with floating ambient 3D depth particles.
3. **VisionOS-Grade Liquid Glass Material**: 50px backdrop blur, dynamic mouse-following specular border luminescence, and dual-layer specular rims.

---

## 2. Technical Architecture

### Component: `frontend/src/components/LiquidGlassCanvas.tsx`
- **Spline Curve Smoothing**:
  - Store recent pointer points with timestamps.
  - Calculate smooth Bezier/Catmull-Rom interpolation through points to eliminate sharp polygonal angles.
  - Apply additive blending (`ctx.globalCompositeOperation = 'screen'`).
  - Emit subtle floating stardust particles on motion with velocity decay.
- **Volumetric 3D Crystal Gem Engine**:
  - Define 3D polyhedron meshes with vertices, edge lists, and triangular/quadrilateral face definitions.
  - Calculate face normal vectors: $\vec{N} = (\vec{B} - \vec{A}) \times (\vec{C} - \vec{A})$.
  - Project light vector from cursor position to face centroid.
  - Calculate diffuse and specular intensity: $I = \max(0, \vec{N} \cdot \vec{L})$.
  - Render semi-transparent shaded face fills (`rgba(255, 255, 255, alpha * I)`) + crisp hairline edge borders.
- **Floating 3D Ambient Dust**:
  - 40 ambient particles distributed in 3D volume $[-width/2, width/2] \times [-height/2, height/2] \times [-300, 300]$.
  - Soft radial glows scaled by depth $z$.

### Styling: `frontend/src/index.css` & `frontend/src/App.tsx`
- Refined glass surfaces:
  - `backdrop-filter: blur(50px) saturate(240%) contrast(108%)`.
  - Double specular rim: `box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.45), inset 0 0 0 1px rgba(255, 255, 255, 0.12), 0 24px 60px -12px rgba(0, 0, 0, 0.8)`.
  - Dynamic cursor distance tracking for interactive card border sheen.

---

## 3. Constraints & Verification

- 100% strict monochrome aesthetic (obsidian, silver, platinum, crystal white).
- Zero third-party 3D engine dependencies.
- Zero TypeScript or Vite compilation errors (`npm run build`).
- Full backend pytest suite (40/40 tests) must pass.

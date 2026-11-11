# 3D Liquid Glass & Interactive Cursor Light Trail Design

**Date:** 2026-11-11  
**Author:** oynu & Antigravity (Google DeepMind)  
**Status:** Approved

---

## 1. Intent & Purpose

Transform Viddy's user experience into a premium, tactile Apple VisionOS-inspired environment featuring:
1. **Interactive Cursor Light Trail**: An ethereal luminous trail and ambient spotlight that follows the user's mouse and diffuses through frosted glass surfaces.
2. **Monochrome 3D Depth Field**: A lightweight, 60fps native HTML5 Canvas background with floating 3D geometric facets and perspective grid in obsidian and silver, responding with subtle mouse parallax.
3. **Hyper-Translucent Glass Surfaces**: Deepened glass refraction (`backdrop-filter: blur(40px) saturate(220%)`), dual-tier specular edge bevels, and translucent gradient fills.

---

## 2. Technical Architecture

### Component: `frontend/src/components/LiquidGlassCanvas.tsx`
- **Render Engine**: Hardware-accelerated 2D canvas context using pure JavaScript matrix math for 3D perspective projection.
  - Zero heavy 3D library dependencies (no Three.js overhead); bundle stays ultra-lightweight (<10KB).
- **3D Geometry**:
  - Floating 3D polyhedron facets (icosahedron / faceted crystals) rendered with translucent strokes (`rgba(255, 255, 255, 0.15)` to `0.04`).
  - Subtle rotating drift and mouse-driven parallax translation (`lerp` smoothed).
- **Cursor Light Trail**:
  - Captures `pointermove` coordinates.
  - Maintains a history queue of recent points with timestamp-based decay.
  - Renders a multi-stop radial gradient spotlight directly at cursor position (`rgba(255, 255, 255, 0.15)` fading to transparent at 280px radius).
  - Renders a smooth light wake connecting recent cursor positions with fading alpha and gaussian-like glow.
- **Accessibility & Performance**:
  - Checks `window.matchMedia('(prefers-reduced-motion: reduce)')`. If reduced motion is requested, freezes rotation/parallax and renders a static ambient glow.
  - Uses `requestAnimationFrame` loop with resize observer and auto-pauses when tab is hidden (`document.hidden`).

### Styling: `frontend/src/index.css` & `frontend/src/App.tsx`
- Increase glass transparency so the 3D canvas and light trail are visibly refracted behind all UI elements.
- Specular edge highlights with crisp 1.5px bevels (`box-shadow: inset 0 1.5px 1px 0 rgba(255, 255, 255, 0.35)`).
- Dropzone and cards upgraded with reactive hover border highlights.

---

## 3. Verification & Safety Constraints

- **Strict Monochrome**: Stick to Apple dark mode monochrome (obsidian, silver, platinum, white highlights).
- **Zero Build Failures**: Full TypeScript compilation (`tsc && vite build`) and 40/40 pytest backend tests passing.
- **Performance Budget**: Target constant 60 FPS on standard desktop displays.

# VisionOS Liquid Glass & Volumetric 3D Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Catmull-Rom spline liquid light trail, 3D volumetric glass gems with normal-based surface lighting, and VisionOS-grade frosted glass styling.

**Architecture:** Upgraded 2D canvas engine with normal-vector facet shading and spline curve interpolation in `frontend/src/components/LiquidGlassCanvas.tsx`, combined with enhanced glass styling in `frontend/src/index.css` and `frontend/src/App.tsx`.

**Tech Stack:** React 18, TypeScript, HTML5 Canvas, Tailwind CSS, Vite.

**Spec:** `docs/superpowers/specs/2026-11-11-visionos-liquid-glass-v2-design.md`

## Global Constraints

- Pure Canvas API (zero external 3D libraries).
- Strict monochrome palette: obsidian black, silver, and crystal highlights.
- Zero TypeScript or Vite compilation errors (`npm run build`).
- All 40 pytest tests must pass without regressions.
- Full respect for `prefers-reduced-motion`.

## Review Focus

1. Spline interpolation produces smooth continuous curves without knotting or inflection artifacts.
2. 3D face normals correctly illuminate faces facing the cursor light source.
3. Canvas performance maintains steady 60 FPS without memory leaks from particle queues.
4. Glass panels maintain high contrast readability over 3D gems.
5. All buttons and interactive drop zones retain responsive hover and drag-and-drop behavior.

---

### Task 1: Overhaul LiquidGlassCanvas with Splines, 3D Shaded Gems & Stardust

**Files:**
- Modify: `frontend/src/components/LiquidGlassCanvas.tsx`

**Interfaces:**
- Produces: `<LiquidGlassCanvas />` with volumetric 3D gem facets, Catmull-Rom spline trail, and ambient depth particles.

- [ ] **Step 1: Implement Catmull-Rom spline curve generator**
  Interpolate smooth Bezier control points across cursor trail coordinates with smooth tapering and additive blending.

- [ ] **Step 2: Implement 3D Face Normal Shading for Volumetric Crystal Polyhedra**
  Define face indices for floating polyhedra, compute 3D cross-product normals, dot with cursor light vector, and render semi-transparent illuminated glass faces.

- [ ] **Step 3: Add 3D Ambient Dust Particles & Stardust Dissolve**
  Add 3D depth particles and decaying cursor stardust sparks.

---

### Task 2: Enhance VisionOS Frosted Glass Styling in CSS & App.tsx

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Produces: VisionOS-grade `.glass-panel`, `.glass-card`, `.glass-dropzone` with 50px blur, double-hairline specular bevels, and dynamic border luminescence.

- [ ] **Step 1: Update CSS glass utilities**
  Update `.glass-panel`, `.glass-card`, `.glass-dropzone`, `.glass-modal` in `frontend/src/index.css` with double specular rims and 50px backdrop blur.

- [ ] **Step 2: Add mouse-aware specular sheen in App.tsx**
  Add subtle mouse coordinates tracking on container to cast dynamic edge sheen across glass cards.

---

### Task 3: Build, Verify & Git Synchronization

**Files:**
- Verify: `frontend/dist`

- [ ] **Step 1: Compile frontend bundle**
  Run `cmd.exe /c "cd frontend && npm.cmd run build"` and verify exit code 0.

- [ ] **Step 2: Run backend test suite**
  Run `.\.venv\Scripts\python.exe -m pytest backend/tests/ -v` and verify 40/40 tests pass.

- [ ] **Step 3: Commit and push**
  Commit all changes and push to `origin main`.

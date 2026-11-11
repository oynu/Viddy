# 3D Liquid Glass & Interactive Cursor Light Trail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an interactive 3D background canvas with a luminous cursor light trail and hyper-translucent liquid glass UI.

**Architecture:** Native HTML5 2D canvas with 3D wireframe perspective projection and decaying cursor trail buffer in `frontend/src/components/LiquidGlassCanvas.tsx`, combined with enhanced glassmorphism styles in `frontend/src/index.css` and `frontend/src/App.tsx`.

**Tech Stack:** React 18, TypeScript, HTML5 Canvas, Tailwind CSS, Vite.

**Spec:** `docs/superpowers/specs/2026-11-11-3d-liquid-glass-light-trail-design.md`

## Global Constraints

- Zero external 3D libraries (keep lightweight, vanilla Canvas 2D projection math).
- Strict monochrome palette: black, white, silver, and translucent highlights.
- Zero TypeScript or Vite compilation errors (`npm run build`).
- All 40 pytest tests must pass without regressions.
- Full respect for `prefers-reduced-motion`.

## Review Focus

1. Canvas resizes smoothly on window resize without distortion or memory leaks.
2. Animation loop pauses cleanly when browser tab is inactive (`visibilitychange`).
3. Cursor light trail decays smoothly without stutter or frame drops.
4. Glass panels refract the cursor light visibly when hovered.
5. All buttons and interactive elements remain clickable with `pointer-events-none` on background canvas.

---

### Task 1: Create LiquidGlassCanvas Component with 3D Depth & Light Trail

**Files:**
- Create: `frontend/src/components/LiquidGlassCanvas.tsx`

**Interfaces:**
- Produces: `<LiquidGlassCanvas />` React component mounting a fullscreen, fixed, pointer-events-none canvas.

- [ ] **Step 1: Implement 3D math and particle trail data structures**
  Define point structures, 3D projection formulas, polyhedron vertices, and light trail queue.

- [ ] **Step 2: Implement animation loop and event listeners**
  Add `pointermove` tracking with decaying trail points, 60fps `requestAnimationFrame` loop, resize listener, and `prefers-reduced-motion` detection.

- [ ] **Step 3: Render 3D geometric facets & cursor spotlight**
  Draw floating rotating facets in monochrome translucency and draw cursor spotlight + luminous fading trail.

---

### Task 2: Enhance Hyper-Translucent Glass Styles in CSS

**Files:**
- Modify: `frontend/src/index.css`

**Interfaces:**
- Produces: Refined `.glass-panel`, `.glass-card`, `.glass-dropzone`, `.glass-modal` with increased translucency (`blur(40px)`, multi-tier bevels).

- [ ] **Step 1: Increase glass transparency and blur**
  Update glass backgrounds to translucent gradient washes (`rgba(255, 255, 255, 0.07)` to `0.015`) and `backdrop-filter: blur(40px) saturate(220%)`.

- [ ] **Step 2: Add dual-tier specular edge highlights**
  Add sharp top bevel reflection `box-shadow: inset 0 1.5px 1px 0 rgba(255, 255, 255, 0.35)` to simulate real glass edge refraction.

---

### Task 3: Integrate LiquidGlassCanvas in App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `<LiquidGlassCanvas />` from `frontend/src/components/LiquidGlassCanvas.tsx`.

- [ ] **Step 1: Mount LiquidGlassCanvas at root level**
  Import and mount `<LiquidGlassCanvas />` as the top-level fixed background.

- [ ] **Step 2: Ensure glass surfaces allow light transmission**
  Ensure all article cards, floating header, and dropzone maintain proper z-index and translucency to let the 3D depth and cursor light shine through.

---

### Task 4: Compilation, Verification & Git Synchronization

**Files:**
- Verify: `frontend/dist`

- [ ] **Step 1: Run frontend compilation**
  Run `cmd.exe /c "cd frontend && npm.cmd run build"` and verify exit code 0.

- [ ] **Step 2: Run backend pytest test suite**
  Run `.\.venv\Scripts\python.exe -m pytest backend/tests/ -v` and verify 40/40 tests pass.

- [ ] **Step 3: Commit and push to GitHub**
  Commit all changes to git and push to `origin main`.

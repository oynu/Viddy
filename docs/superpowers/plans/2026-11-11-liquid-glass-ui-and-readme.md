# Liquid Glass UI & README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevate Viddy to an Apple-inspired Liquid Glass (frosted glass) interface while updating `README.md` with multi-browser support, security details, and repository contributors.

**Architecture:** Tailwind CSS glassmorphism styling (`backdrop-blur-2xl`, specular top-edge highlights, translucent borders, ambient top radial glow) coupled with streamlined React component layout in `frontend/src/App.tsx`, accompanied by comprehensive documentation in `README.md`.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Lucide React, FastAPI, Vite, Pytest.

**Spec:** `docs/superpowers/specs/2026-11-11-liquid-glass-ui-and-readme-design.md`

## Global Constraints

- Preserve strict monochrome minimalist color scheme (obsidian black, frosted white transparencies, crisp typography).
- Zero TypeScript errors (`tsc && vite build`).
- All 40 pytest tests must pass without regressions.
- No personal user paths or unmasked secrets in any committed files.

## Review Focus

1. Drop zone maintains drag-over visual feedback smoothly without layout jitter.
2. Frosted glass cards remain readable with strong contrast against thumbnails and text.
3. Modal background blur prevents interaction with underlying elements when open.
4. Active browser detection label renders smoothly inside glass pills.
5. All external links and copy actions work cleanly without unexpected re-renders.

---

### Task 1: Update README.md with Multi-Browser Engine & Contributors

**Files:**
- Modify: `README.md`

**Interfaces:**
- Documents: `backend/publishing/browser_utils.py`, `backend/api/routes.py`, `frontend/src/App.tsx`

- [ ] **Step 1: Update repository clone URL**
  Set remote origin to `https://github.com/oynu/Viddy.git`.

- [ ] **Step 2: Update browser compatibility matrix**
  Document native support for Brave, Google Chrome, Microsoft Edge, Chromium, and Playwright engine fallback. Include `BROWSER_PATH` environment override documentation.

- [ ] **Step 3: Update Drop & Auto-Publish workflow**
  Document speech transcription, viral hook/caption generation, and automated posting upon drop.

- [ ] **Step 4: Add Contributors section**
  Add Contributors section crediting `@oynu` (Creator & Lead) and `Antigravity (Google DeepMind)` (Core Architecture & Implementation).

- [ ] **Step 5: Verify markdown formatting**
  Verify markdown headings, code blocks, and links render cleanly.

---

### Task 2: Implement Apple-Style Liquid Glass Styles in CSS

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/tailwind.config.js` (if needed)

**Interfaces:**
- Produces: CSS utility classes for ambient glow, frosted glass surfaces, and specular highlights.

- [ ] **Step 1: Add ambient radial lighting to body**
  Add subtle top radial luminance (`radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.05) 0%, rgba(0, 0, 0, 1) 75%)`) and enhanced font smoothing.

- [ ] **Step 2: Define liquid glass utility classes**
  Define `.glass-panel`, `.glass-pill`, `.glass-card`, `.glass-modal` with `backdrop-filter: blur(24px)`, `background: rgba(255, 255, 255, 0.03)`, `border: 1px solid rgba(255, 255, 255, 0.08)`, and `box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12)`.

- [ ] **Step 3: Define refined scrollbars and hover micro-sheens**
  Ensure scrollbars and button transitions align with Apple dark mode design standards.

---

### Task 3: Refactor App.tsx to Liquid Glass Interface

**Files:**
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: CSS glass utilities from `frontend/src/index.css`.
- Produces: Refined liquid glass UI layout.

- [ ] **Step 1: Refactor Header and Platform Pills**
  Make header floating frosted glass with top highlight; convert platform badges into tactile glass capsules.

- [ ] **Step 2: Refactor Target Selector & Auto-Post Checkbox**
  Style destination tabs with an Apple-style segmented glass switcher.

- [ ] **Step 3: Refactor Drop Zone**
  Elevate drop zone into a liquid glass container with subtle center radial sheen, animated hover border, and polished typography.

- [ ] **Step 4: Refactor Video Cards**
  Apply frosted glass container with specular edge, refined metadata sections (captions, tags, pinned comments), and floating glass action buttons.

- [ ] **Step 5: Refactor Platform Channels Modal**
  Transform modal into a frosted glass sheet with backdrop blur overlay and elegant inputs.

---

### Task 4: Frontend Build & Verification

**Files:**
- Verify: `frontend/dist`

- [ ] **Step 1: Run frontend compilation**
  Run `cmd.exe /c "cd frontend && npm.cmd run build"` and verify exit code 0.

- [ ] **Step 2: Run pytest test suite**
  Run `.\.venv\Scripts\python.exe -m pytest backend/tests/ -v` and verify 40/40 tests pass.

- [ ] **Step 3: Commit and push**
  Commit all changes to git and push to `origin main`.

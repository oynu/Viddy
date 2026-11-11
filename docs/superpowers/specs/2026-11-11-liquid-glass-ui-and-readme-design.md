# Viddy Liquid Glass UI & README Architecture Design

**Date:** 2026-11-11  
**Author:** oynu & Antigravity (Google DeepMind)  
**Status:** Approved

---

## 1. Intent & Purpose

Transform the Viddy user interface into a high-end, Apple-inspired **Liquid Glass (frosted glass / glassmorphism)** aesthetic while strictly preserving the minimalist monochrome identity that the user loves. Concurrently, overhaul `README.md` to accurately document all recent architecture additions (multi-browser auto-detection, audio transcription, viral metadata generation, file upload security guards) and formally establish repository contributors.

---

## 2. Goals, Non-Goals & Constraints

### Goals
- **Liquid Glass Aesthetic**:
  - Replace flat dark containers with Cupertino-style frosted glass surfaces: `backdrop-blur-2xl`, translucent fills (`rgba(255, 255, 255, 0.03)`), delicate hairline borders (`rgba(255, 255, 255, 0.08)`), and top specular highlights (`inset 0 1px 0 rgba(255, 255, 255, 0.12)`).
  - Ambient depth: Deep obsidian background (`#000000`) with subtle radial ambient glow emanating from the top.
  - Micro-interactions: Tactile glass buttons, smooth hover transitions, and refined typography.
  - Frosted modal dialogue floating over an ambient backdrop blur.
- **Accurate Documentation**:
  - Document multi-browser detection across Windows, macOS, and Linux (Brave, Chrome, Edge, Chromium, and Playwright engine fallback).
  - Detail `BROWSER_PATH` environment override.
  - Document video drop auto-publishing, speech recognition transcription, and viral metadata algorithms.
  - Set repository clone origin to `https://github.com/oynu/Viddy.git`.
  - Add Contributors section honoring `@oynu` and `Antigravity (Google DeepMind)`.

### Non-Goals
- Do not introduce distracting saturated color themes; preserve the clean monochrome / black-and-white identity.
- Do not break existing API contracts, database schema, or publishing workflows.

### Constraints
- Zero TypeScript or CSS compilation errors.
- Full backend pytest suite must pass with 0 failures (40/40 tests).
- All security hardening (whitelisting, path traversal guards) must remain intact.

# README Visual Narrative V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a coherent visual narrative to the China Travel Assistant README while preserving its top GIF and installation-first workflow.

**Architecture:** Keep all visuals local under `assets/readme/`. Use existing JPEGs for a theme-aware journey overview, deterministic SVGs for topology and safety concepts, and Markdown for all copyable commands, URLs, credentials, and detailed source lists.

**Tech Stack:** Markdown, SVG 1.1-compatible XML, JPEG, GIF, Python unittest, macOS `sips`, Ruff, Gitleaks, Codex plugin validator.

---

### Task 1: Add visual publication contracts

**Files:**
- Modify: `tests/test_readme.py`

- [ ] Add a test requiring the eight named SVG files and at least eleven local image references in `README.md`.
- [ ] Add XML checks for `<title>`, `<desc>`, a `1200`-unit viewBox, and absence of `script`, `foreignObject`, remote URLs, and key-like values.
- [ ] Add a test requiring `<picture>` with the existing dark and light JPEG assets.
- [ ] Run `PYTHONPATH=plugins/china-travel-assistant/src python3 -m unittest tests.test_readme -v` and confirm it fails because the assets are absent.

### Task 2: Create section rhythm assets

**Files:**
- Create: `assets/readme/section-quickstart.svg`
- Create: `assets/readme/section-routing.svg`
- Create: `assets/readme/section-security.svg`
- Create: `assets/readme/section-sources.svg`

- [ ] Build four 1200x96 SVG headers using shared route-marker grammar and distinct section codes.
- [ ] Keep essential titles at or above 40 SVG units and include accessible metadata.
- [ ] Run the focused README test and confirm section assets pass their structural contracts.

### Task 3: Create information schematics

**Files:**
- Create: `assets/readme/skill-system-map.svg`
- Create: `assets/readme/provider-workflow.svg`
- Create: `assets/readme/credential-boundary.svg`
- Create: `assets/readme/provenance-map.svg`

- [ ] Build the Skill hub-and-spoke diagram around `$plan-china-trip` and the five execution Skills.
- [ ] Build the four-stage provider workflow with an explicit conditional verification gate.
- [ ] Build the dual-chamber credential boundary with `0600` local storage and `NO_KEYS_PRESENT` external surfaces.
- [ ] Build the three-column provenance matrix without duplicating the full Markdown project inventory.
- [ ] Run the focused README test and confirm all SVG structural contracts pass.

### Task 4: Integrate the complete visual sequence

**Files:**
- Modify: `README.md`
- Modify: `assets/readme/README.md`

- [ ] Embed the existing JPEGs through a theme-aware `<picture>` immediately after the project summary.
- [ ] Replace four Markdown section headings with their corresponding lightweight SVG headers while retaining accessible HTML headings where needed.
- [ ] Insert each information schematic next to the Markdown section it explains.
- [ ] Update the asset ledger with each asset's communication job and source type.
- [ ] Run the focused README tests and confirm at least eleven local visual references are present.

### Task 5: Render and verify

**Files:**
- Modify only deterministic defects found during rendering.

- [ ] Render every SVG to PNG with `sips` and build desktop and mobile contact sheets for visual review.
- [ ] Run `python3 /tmp/audit_beautify_readme.py README.md` and verify all local images exist.
- [ ] Run all unittests, Ruff, Plugin validation, Gitleaks, local-link checks, and `git diff --check`.
- [ ] Commit the final verified visual narrative as atomic documentation changes.

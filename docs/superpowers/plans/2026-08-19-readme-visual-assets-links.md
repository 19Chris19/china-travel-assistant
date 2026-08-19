# README Visual Assets And Source Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the China Travel Assistant GitHub homepage installation-first, place the approved GIF at the top, and document credential links, upstream sources, and a safe Codex deployment prompt.

**Architecture:** Keep visual assets local under `assets/readme/`; keep searchable copy, commands, links, and safety rules in Markdown. Treat `credentials.md` and the three provenance documents as the authoritative audit layer, with README linking to them instead of duplicating unverified claims.

**Tech Stack:** Markdown, JPEG, GIF, Python unittest, plugin validator, Ruff, Gitleaks, ffprobe.

---

### Task 1: Add approved README assets

**Files:**
- Create: `assets/readme/china-travel-assistant.gif`
- Create: `assets/readme/china-travel-assistant-dark.jpeg`
- Create: `assets/readme/china-travel-assistant-light.jpeg`
- Create: `assets/readme/README.md`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Write the failing asset contract test**

Add tests that require the three files, require the README asset note, and assert the GIF media metadata is `640x271`, ten frames per second, and below `2 MB`.

- [ ] **Step 2: Run the focused test and confirm it fails**

Run `PYTHONPATH=plugins/china-travel-assistant/src python3 -m unittest tests.test_readme -v`. Expected failure: the asset files and/or test module do not yet exist.

- [ ] **Step 3: Copy the user-provided assets without re-encoding**

Copy the GIF and two JPEGs from `/Users/chrislee/Downloads/` into `assets/readme/`. Preserve the GIF byte stream and record source dimensions and intended placement in `assets/readme/README.md`.

- [ ] **Step 4: Run the focused test and confirm it passes**

Run the same unittest command. Expected result: all asset contract assertions pass.

- [ ] **Step 5: Commit the asset-only change**

Run `git add assets/readme tests/test_readme.py` and commit with `docs(readme): add approved travel assistant visual assets`.

### Task 2: Rewrite the installation-first README

**Files:**
- Modify: `README.md`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Add failing README behavior assertions**

Extend `tests/test_readme.py` to require that the first image reference is `assets/readme/china-travel-assistant.gif`, that the README contains the real Release/CI/License links, all six skill names, all credential variable names, all three provenance relationship labels, and the deployment prompt safety phrases.

- [ ] **Step 2: Run the focused test and confirm it fails**

Run `PYTHONPATH=plugins/china-travel-assistant/src python3 -m unittest tests.test_readme -v`. Expected failure: the current README lacks the top GIF and the complete installation/source/prompt structure.

- [ ] **Step 3: Implement the Markdown information architecture**

Rewrite `README.md` so the first non-heading visual is the local GIF, followed by a concise Chinese description, status badges, the three-minute install path, first conversation, capability matrix, provider routing, credentials links, a `<details>`-wrapped Codex deployment prompt, provenance links, safety boundaries, development checks, and a static asset note.

- [ ] **Step 4: Run the focused test and confirm it passes**

Run the same unittest command and inspect the rendered Markdown source for copyable commands and valid local links.

- [ ] **Step 5: Commit the README change**

Run `git add README.md tests/test_readme.py` and commit with `docs(readme): make homepage installation first`.

### Task 3: Complete credential application and configuration documentation

**Files:**
- Modify: `plugins/china-travel-assistant/references/credentials.md`
- Modify: `README.md`
- Test: `tests/test_readme.py`

- [ ] **Step 1: Add failing credential-link assertions**

Require the README and credential reference to include the AMap Web Service console, AMap JS API prerequisites, FlyAI, Variflight, and the local configuration path, while ensuring no sample line contains a non-empty secret value.

- [ ] **Step 2: Run the focused test and confirm it fails**

Run `PYTHONPATH=plugins/china-travel-assistant/src python3 -m unittest tests.test_readme -v`. Expected failure: the current reference lacks step-by-step acquisition and configuration guidance.

- [ ] **Step 3: Document safe setup instructions**

Add provider-by-provider purpose, official application URL, console/configuration URL, variable name, optionality, quota caveat, `0600` storage rule, environment override behavior, and `travel-assistant doctor` commands. Keep `VIGOLIVE_API_KEY` explicitly labeled as a v2 reservation.

- [ ] **Step 4: Run the focused test and confirm it passes**

Run the same unittest command and verify the docs contain no actual key-like strings.

- [ ] **Step 5: Commit the credential documentation**

Run `git add plugins/china-travel-assistant/references/credentials.md README.md tests/test_readme.py` and commit with `docs(credentials): document official application and setup links`.

### Task 4: Verify links, assets, security, and package behavior

**Files:**
- Modify: `tests/test_readme.py` only if a discovered deterministic contract is missing.

- [ ] **Step 1: Run focused asset metadata checks**

Run `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames,duration -of json assets/readme/china-travel-assistant.gif` and `stat -f '%z' assets/readme/china-travel-assistant.gif`. Expected: `640x271`, `10/1`, `52` frames, about `5.33` seconds, and fewer than `2097152` bytes.

- [ ] **Step 2: Run all repository tests**

Run `PYTHONPATH=plugins/china-travel-assistant/src python3 -m unittest discover -s tests -v`. Expected: all tests pass, including the new README contract.

- [ ] **Step 3: Run static checks and plugin validation**

Run `ruff check --isolated --select E4,E7,E9,F plugins/china-travel-assistant/src plugins/china-travel-assistant/skills/plan-china-trip/scripts tests` and `python3 /Users/chrislee/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/china-travel-assistant`. Expected: no Ruff errors and valid Plugin output.

- [ ] **Step 4: Run secret and link checks**

Run `gitleaks detect --no-banner --redact --source .` and a deterministic Python link check over local Markdown targets and `https://` URL syntax. Expected: no secret findings and no missing local targets.

- [ ] **Step 5: Inspect the final diff and commit verification metadata**

Run `git diff --check`, `git status --short`, and `git diff --stat`. Review that only the requested README, docs, tests, and assets changed; then commit with `chore(readme): verify homepage publication assets`.

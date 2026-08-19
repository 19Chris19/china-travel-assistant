---
name: verify-travel-web
description: Verify dynamic travel pages using Ego Browser task spaces and the user's existing login state. Use only when API or MCP data is unavailable, login-specific prices or room inventory must be checked, or the user asks to inspect a booking page; pause for user handoff on login, captcha, real-name, or payment.
---

# Verify Travel Web

Ego Browser is the only browser automation layer in this project. Do not use another browser driver or bridge.

## Workflow

1. Use `ego-browser nodejs <<'EOF'` and create or reuse a named task space for the current travel goal.
2. Open only the requested official or platform URL. Observe with `snapshotText()` or `captureScreenshot()` before acting.
3. Extract page facts with their URL, visible timestamp if present, currency, room/fare context, and whether the user appears logged in.
4. Never export cookies, storage state, tokens, passwords, identity numbers, payment details, or QR codes into files or chat.
5. If login, CAPTCHA, 2FA, real-name verification, payment, order submission, or a page warning requires user action, hand off the task space and wait for explicit continuation.
6. Keep page evidence separate from API/MCP results. Explain conflicts instead of silently choosing one.
7. Close the task space when finished unless the user explicitly asks to keep the page open for manual action.

Reading results, selecting filters, opening detail pages, scrolling, screenshots, and filling non-sensitive search criteria are allowed. Purchase, payment, real-name entry, cancellation, refund, and change actions require separate explicit confirmation and remain out of scope for this Skill.

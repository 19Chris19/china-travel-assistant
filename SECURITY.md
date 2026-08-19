# Security Policy

## Secrets

Never commit API keys, cookies, browser profiles, authorization headers, identity documents, order numbers, QR codes, or payment data.

Store provider keys in ~/.config/china-travel-assistant/credentials.env. The file must use mode 0600. Runtime diagnostics report only state labels and never secret values.

Keys previously pasted into chat, committed to a file, or embedded in generated URLs must be considered exposed and rotated before publication.

## Browser State

Ego Browser owns login-state reuse. Do not export cookies or storage state into this repository. Human handoff is mandatory for CAPTCHA, 2FA, real-name verification, order submission, payment, cancellation, refund, and ticket changes.

## Reporting

Use GitHub private vulnerability reporting for the repository. Do not include a real key, cookie, identity number, or payment detail in an issue.

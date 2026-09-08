# Quickstart: CI Frontend Unit Tests

## Local parity (same as CI Node steps)

```bash
npm ci   # or npm install if already bootstrapped
npm run check
npm run test:performance-ui
npm run test:rss
```

Optional focused debug (not required in CI):

```bash
npm run test:static-nav
```

## What changed in CI

`.github/workflows/ci.yml` Install-and-check step chains the two unit scripts
after `npm run check`.

## Issue

Fixes the gap described in GitHub #98 / TD-001.

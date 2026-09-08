# Feature Specification: Gitignore Playwright MCP artifacts

**Feature Branch**: `tech-debt/100-daily-i18n-tests` (batch with approved auto-fix)
**Created**: 2026-09-08
**Status**: Done
**GitHub Issue**: #105 / TD-009

## User Story 1 - Ignore local Playwright MCP output (P1)

As a contributor, `.playwright-mcp/` stays untracked so screenshots/yml cannot be committed by mistake.

**Acceptance**: `.gitignore` contains `.playwright-mcp/`; `git check-ignore -v .playwright-mcp/` matches.

## Edge Cases (brainstorm auto)

- Only `.playwright-mcp/` (issue scope). `.serena/` left alone unless separately filed.
- Do not delete existing local folder contents.

## Requirements

- **FR-001**: Add `.playwright-mcp/` to `.gitignore`
- **Non-Goal**: Force-remove from history (never tracked)

## Brainstorm Log

- 2026-09-08: Auto — ignore path only; no cleanup commit of folder.

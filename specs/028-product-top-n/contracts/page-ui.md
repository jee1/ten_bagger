# Contract: Day-page Top-N UI

## Surface

- **In scope**: `DailyCard.astro` when `entry.topCandidates` is present
  (index + `/daily/[date]`).
- **Out of scope**: `archive.astro` / `Calendar.astro` chrome (no badges,
  no inline expand on archive list).

## Behavior

1. Default: Top-N section **collapsed** (`<details>` or equivalent).
2. Collapsed first viewport: existing one-pick / no_pick narrative unchanged
   (no new card cluster in hero).
3. Expanded: ordered list/table of up to 5 rows — rank, symbol, localized
   name, composite + axis scores (reuse existing score label tokens).
4. Missing `topCandidates`: render nothing for this section.
5. Framing copy (i18n): transparency / runners-up — not additional picks.
6. Preserve global investment disclaimer elsewhere on layout.

## A11y

- Native disclosure control preferred (`details`/`summary`) for keyboard
  and screen readers.
- Score numbers remain text (not color-only meaning).

## Locales

- KR/EN labels for section title + short helper line.
- Numeric scores identical across locales.

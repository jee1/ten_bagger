# Quickstart: Performance Loop docs gate

**Goal**: Assemble one reviewable architecture package and close the docs gate
(Issue #75 / Epic #74) without changing Score/pick behavior.

## Prerequisites

- Branch `018-performance-loop-docs` (or equivalent docs PR branch)
- Spec: `specs/018-performance-loop-docs/spec.md` (Brainstormed / ready for plan)
- Checklist stub: `specs/018-performance-loop-docs/checklists/architecture-gate.md`

## Steps

1. **Skeleton**  
   Create paths from `contracts/package-tree.md`. Write
   `docs/architecture/README.md` with reading order, eng-authority note
   (vs Methodology), and Score v2 freeze note.

2. **C4 (Mermaid)**  
   Author `c4/context.md`, `container.md`, `component.md`. Keep node/edge labels
   readable as text if Mermaid fails to render.

3. **arc42 + risks**  
   Fill FR-005 sections in `arc42.md` (no placeholders). Include four-axis risk
   check (contamination, look-ahead, overfitting, ops failure).

4. **Glossary**  
   `glossary.md` with EN definitions + KO glosses for: pick, no_pick, PIT, OOS,
   GO/NO-GO, ledger, forward return.

5. **ADRs**  
   Write `adr/0001`–`0004` (FR-006 topics). Each: Context / **one** preferred
   Decision / Consequences. Status may be Proposed.

6. **Draft schemas**  
   Copy `contracts/*.schema.draft.json` → `scripts/schema/`. Do **not** wire into
   `validate:content` or `gen:types`. Optional local check (`jsonschema` installed):

   ```bash
   python3 -c "import json; from jsonschema import Draft202012Validator; from pathlib import Path
   root=Path('specs/018-performance-loop-docs/contracts')
   for s,e in [('ledger.schema.draft.json','examples/ledger.example.json'),('performance-artifact.schema.draft.json','examples/performance-artifact.example.json')]:
     Draft202012Validator(json.loads((root/s).read_text())).validate(json.loads((root/e).read_text())); print('OK', e)"
   ```

7. **Issue mapping**  
   Create `specs/018-performance-loop-docs/issue-mapping.md` from
   `contracts/issue-labels.md`.

8. **Pointers & issues**  
   Root README one-paragraph pointer. Link Epic #74 and #75 to the architecture
   index. SHOULD comment #63/#64/#66/#67 with paths.

9. **Path allowlist review**  
   Confirm PR diff stays within FR-026 allowlist (no scoring/pick logic).

10. **Gate checklist**  
    Complete `architecture-gate.md` (second-person or dated self-attestation).
    Declare gate done only when FR-025 package is complete in one reviewable set.

## Done when

- SC-001…SC-011 satisfiable from the package alone  
- Checklist outcome Pass (or Pass with tracked follow-ups)  
- Zero intentional Score weight / pick-logic diffs in the docs PR  

## Next

`/speckit.superspec.tasks` → implement docs per task list → open docs PR.

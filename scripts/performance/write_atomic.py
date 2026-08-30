"""Atomic replace for ledger/performance JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


def atomic_replace(
    writes: dict[Path, dict[str, Any]],
    validators: list[jsonschema.Draft202012Validator],
    *,
    dry_run: bool = False,
) -> None:
    """Write temps, validate, rename — failure leaves committed files untouched."""
    if len(validators) != len(writes):
        raise ValueError("validators length must match writes")
    temps: list[tuple[Path, Path]] = []
    try:
        for (path, data), validator in zip(writes.items(), validators):
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errors:
                err = errors[0]
                loc = ".".join(str(p) for p in err.path) or "(root)"
                raise ValueError(f"{path}: {loc}: {err.message}")
            temp = path.with_name(path.name + ".tmp")
            temp.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            temps.append((temp, path))
        if dry_run:
            for temp, _ in temps:
                temp.unlink(missing_ok=True)
            return
        for temp, final in temps:
            temp.replace(final)
    except Exception:
        for temp, _ in temps:
            temp.unlink(missing_ok=True)
        raise

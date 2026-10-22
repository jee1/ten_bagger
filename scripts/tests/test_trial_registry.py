"""The committed trial registry lists every run artifact."""

from __future__ import annotations

from trial_registry import REGISTRY_PATH, ROOT, render


def test_committed_registry_matches_artifacts():
    assert REGISTRY_PATH.read_text() == render(), "run: cd scripts && python trial_registry.py"


def test_every_artifact_has_a_row():
    text = render()
    for directory in ("calibration", "walk-forward"):
        for path in (ROOT / "content" / directory).glob("*.json"):
            assert f"`{path.stem}`" in text, path

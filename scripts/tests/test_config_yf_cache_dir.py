"""TEN_BAGGER_YF_CACHE_DIR override for local/systemd runners."""

from __future__ import annotations

import importlib


def test_yf_cache_dir_respects_env(monkeypatch, tmp_path):
    external = tmp_path / "yf"
    monkeypatch.setenv("TEN_BAGGER_YF_CACHE_DIR", str(external))
    import config

    importlib.reload(config)
    assert config.CACHE_DIR == external

    monkeypatch.delenv("TEN_BAGGER_YF_CACHE_DIR", raising=False)
    importlib.reload(config)

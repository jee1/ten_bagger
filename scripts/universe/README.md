# Universe listings

Generated JSON files (`kr.json`, `us.json`) are **not committed** to git.

## Local

```bash
pip install -r scripts/requirements.txt
cd scripts && python build_universe.py
```

## CI

GitHub Actions restores a cache of `scripts/universe/`, runs `build_universe.py` daily, and uses the refreshed listings for screening. The yfinance disk cache key is derived from the built universe files.

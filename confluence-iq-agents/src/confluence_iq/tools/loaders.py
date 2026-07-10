"""Reads JSON / txt from data/ into agent context."""

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent.parent.parent / "data"


def load_customer_data() -> dict:
    path = DATA_DIR / "mock_customer_data.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_seo_trends() -> dict:
    path = DATA_DIR / "mock_seo_trends.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_site_texts() -> dict[str, str]:
    """Return {domain: concatenated text} from site_text/<domain>/*.txt."""
    site_dir = DATA_DIR / "site_text"
    result = {}
    for domain_dir in site_dir.iterdir():
        if domain_dir.is_dir():
            parts = []
            for txt in sorted(domain_dir.glob("*.txt")):
                parts.append(txt.read_text(encoding="utf-8"))
            result[domain_dir.name] = "\n".join(parts)
    return result

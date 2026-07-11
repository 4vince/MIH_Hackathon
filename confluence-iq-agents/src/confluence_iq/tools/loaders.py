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


PROMPTS_DIR = HERE.parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


def load_raw_corpus_text() -> str:
    """Concatenate all raw source data into one text blob for the verifier."""
    import json

    customer_data = json.dumps(load_customer_data())
    seo_trends = json.dumps(load_seo_trends())
    site_texts = "\n".join(load_site_texts().values())
    return "\n".join([customer_data, seo_trends, site_texts])

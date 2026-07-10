"""Run once ahead of time to populate data/site_text/ with scraped site content."""

import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data" / "site_text"

TARGETS = {
    "basilford_com": "https://www.basilford.com",
    "basilfordofniagarafalls_com": "https://www.basilfordofniagarafalls.com",
}

def scrape() -> None:
    for folder_name, url in TARGETS.items():
        target_dir = DATA_DIR / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Scraping {url} -> {target_dir}")
        # TODO: implement fetch + parse + write txt files

if __name__ == "__main__":
    scrape()

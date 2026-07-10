"""Agent 3 output → final .md file in output/."""

import pathlib
from datetime import datetime

from ..schemas import Agent3Output

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "output"


def write_report(output: Agent3Output) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"report_{timestamp}.md"

    lines = [f"# {output.report_title}\n"]
    for section in output.sections:
        lines.append(f"## {section['heading']}\n")
        lines.append(f"{section['body']}\n")

    if output.seo_keyword_targets:
        lines.append("## SEO Keyword Targets\n")
        for kw in output.seo_keyword_targets:
            lines.append(f"- {kw}\n")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)

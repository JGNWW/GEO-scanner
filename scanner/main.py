import datetime as dt
import json
import shutil
from pathlib import Path

import yaml

from .analyzer import score
from .llm import load_providers
from .report import write_csv, write_markdown

ROOT = Path(__file__).resolve().parent.parent


def main():
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    prompts = yaml.safe_load((ROOT / "prompts.yaml").read_text(encoding="utf-8"))

    provider_names = config.get("providers", ["gemini"])
    runs = int(config.get("runs_per_prompt", 1))
    target = config["target"]
    competitors = config.get("competitors", [])

    providers = load_providers(provider_names)
    if not providers:
        raise SystemExit(f"Geen providers geladen uit {provider_names}")

    today = dt.date.today().isoformat()
    rows = []

    for prompt in prompts:
        for provider in providers:
            for run_idx in range(1, runs + 1):
                print(f"[{provider.name}] {prompt['id']} run {run_idx}")
                resp = provider.query(prompt["id"], prompt["text"])
                s = score(resp.answer, resp.citations, target, competitors)

                row = {
                    "date": today,
                    "provider": resp.provider,
                    "model": resp.model,
                    "prompt_id": prompt["id"],
                    "run": run_idx,
                    "target_mentioned": s.target_mentioned,
                    "target_cited": s.target_cited,
                    "target_citation_urls": "|".join(s.target_citation_urls),
                    "competitor_mentions": json.dumps(s.competitor_mentions, ensure_ascii=False),
                    "competitor_citations": json.dumps(
                        {k: len(v) for k, v in s.competitor_citations.items()},
                        ensure_ascii=False,
                    ),
                    "error": resp.error,
                    "_comp_mentions": s.competitor_mentions,
                    "_comp_citations": s.competitor_citations,
                }
                rows.append(row)

    csv_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    write_csv(csv_rows, ROOT / "data" / "results.csv")
    write_markdown(
        today,
        rows,
        prompts,
        target["name"],
        competitors,
        ROOT / "reports" / f"{today}.md",
    )
    _publish_to_docs()
    print(f"Klaar — rapport: reports/{today}.md")


def _publish_to_docs():
    docs = ROOT / "docs"
    if not docs.exists():
        return
    (docs / "data").mkdir(parents=True, exist_ok=True)
    (docs / "reports").mkdir(parents=True, exist_ok=True)

    src_csv = ROOT / "data" / "results.csv"
    if src_csv.exists():
        shutil.copy2(src_csv, docs / "data" / "results.csv")

    reports_dir = ROOT / "reports"
    names = []
    if reports_dir.exists():
        for p in sorted(reports_dir.glob("*.md")):
            shutil.copy2(p, docs / "reports" / p.name)
            names.append(p.name)
    (docs / "reports.json").write_text(json.dumps(names), encoding="utf-8")


if __name__ == "__main__":
    main()

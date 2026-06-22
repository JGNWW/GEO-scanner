import csv
from collections import defaultdict
from pathlib import Path


def write_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "provider",
                "model",
                "prompt_id",
                "run",
                "target_mentioned",
                "target_cited",
                "target_citation_urls",
                "competitor_mentions",
                "competitor_citations",
                "error",
            ],
        )
        if new_file:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def write_markdown(date: str, rows, prompts, target_name: str, competitors, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    prompt_lookup = {p["id"]: p for p in prompts}

    by_prompt = defaultdict(list)
    for r in rows:
        by_prompt[r["prompt_id"]].append(r)

    total = len(rows)
    mentioned = sum(1 for r in rows if r["target_mentioned"])
    cited = sum(1 for r in rows if r["target_cited"])

    comp_mentioned = {c["name"]: 0 for c in competitors}
    comp_cited = {c["name"]: 0 for c in competitors}
    for r in rows:
        for name, v in (r["_comp_mentions"] or {}).items():
            if v:
                comp_mentioned[name] = comp_mentioned.get(name, 0) + 1
        for name, urls in (r["_comp_citations"] or {}).items():
            if urls:
                comp_cited[name] = comp_cited.get(name, 0) + 1

    lines = []
    lines.append(f"# GEO-scan {date}")
    lines.append("")
    lines.append(f"Doel: **{target_name}**  ")
    lines.append(f"Totaal queries: {total}")
    lines.append("")
    lines.append("## Samenvatting")
    lines.append("")
    lines.append("| Organisatie | Genoemd | Geciteerd |")
    lines.append("| --- | ---: | ---: |")
    lines.append(f"| **{target_name}** | {_pct(mentioned, total)} | {_pct(cited, total)} |")
    for c in competitors:
        n = c["name"]
        lines.append(
            f"| {n} | {_pct(comp_mentioned.get(n, 0), total)} | {_pct(comp_cited.get(n, 0), total)} |"
        )
    lines.append("")
    lines.append("## Per prompt")
    lines.append("")

    for pid, results in by_prompt.items():
        p = prompt_lookup.get(pid, {"text": pid, "category": ""})
        lines.append(f"### {pid}")
        lines.append(f"_{p.get('text','')}_  ")
        lines.append(f"Categorie: `{p.get('category','')}`")
        lines.append("")
        for r in results:
            status_mention = "ja" if r["target_mentioned"] else "nee"
            status_cite = "ja" if r["target_cited"] else "nee"
            lines.append(
                f"- **{r['provider']}** (run {r['run']}) — genoemd: {status_mention}, geciteerd: {status_cite}"
            )
            if r["target_citation_urls"]:
                for u in r["target_citation_urls"].split("|"):
                    lines.append(f"    - {u}")
            other_cites = []
            for name, urls in (r["_comp_citations"] or {}).items():
                if urls:
                    other_cites.append(f"{name}: {len(urls)}")
            if other_cites:
                lines.append(f"    - concurrent-citations: {', '.join(other_cites)}")
            if r["error"]:
                lines.append(f"    - fout: {r['error']}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _pct(n: int, total: int) -> str:
    if total == 0:
        return "0 (0%)"
    return f"{n} ({round(100 * n / total)}%)"

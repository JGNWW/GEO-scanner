import re
from dataclasses import dataclass, field
from typing import List
from urllib.parse import urlparse


@dataclass
class Score:
    target_mentioned: bool = False
    target_cited: bool = False
    target_citation_urls: List[str] = field(default_factory=list)
    competitor_mentions: dict = field(default_factory=dict)
    competitor_citations: dict = field(default_factory=dict)


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _contains(text: str, needles) -> bool:
    low = text.lower()
    return any(re.search(rf"\b{re.escape(n.lower())}\b", low) for n in needles)


def score(answer: str, citations: List[str], target: dict, competitors: list) -> Score:
    s = Score()

    target_names = [target["name"]] + target.get("aliases", [])
    target_domains = [d.lower() for d in target.get("domains", [])]

    s.target_mentioned = _contains(answer, target_names + target_domains)

    cited_domains = [_domain(u) for u in citations]
    for url, dom in zip(citations, cited_domains):
        if any(dom == td or dom.endswith("." + td) for td in target_domains):
            s.target_cited = True
            s.target_citation_urls.append(url)

    for comp in competitors:
        name = comp["name"]
        doms = [d.lower() for d in comp.get("domains", [])]
        s.competitor_mentions[name] = _contains(answer, [name] + doms)
        cited = [
            u
            for u, d in zip(citations, cited_domains)
            if any(d == cd or d.endswith("." + cd) for cd in doms)
        ]
        s.competitor_citations[name] = cited

    return s

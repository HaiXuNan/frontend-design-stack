#!/usr/bin/env python3
"""Refresh the catalog from designeer.xyz/resources.

Stdlib only. Network required. Writes data/resources.json, data/resources.csv
and references/catalog.md. Review the diff before committing.

    python scripts/refresh.py [--workers 8]
"""

import argparse
import csv
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

BASE = "https://designeer.xyz"
LISTING = BASE + "/resources"
CATEGORIES = ["Components", "Icons", "Motion & 3D", "Type & Colour"]

# The aggregator also lists paid/promo entries that are not design resources
# and have no category. Keep this list explicit; do not infer from page text.
SKIP_SLUGS = {"discover-useful-apps-ai-tools-websites"}

# Descriptions are fed to the model later, so treat fetched text as untrusted.
# A page that starts issuing instructions or embedding script is not written.
SUSPICIOUS = re.compile(
    r"ignore (all )?(previous|prior) (instructions|prompts)|system prompt|"
    r"you are (chatgpt|an ai)|<script|javascript:",
    re.I,
)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
UA = {"User-Agent": "Mozilla/5.0 (compatible; frontend-design-stack/1.0)"}


def get(url, timeout=30):
    req = Request(url, headers=UA)
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def ld_blocks(html):
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            yield json.loads(raw)
        except json.JSONDecodeError:
            continue


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    for a, b in (("&#x27;", "'"), ("&amp;", "&"), ("&quot;", '"'),
                 ("&#x2F;", "/"), ("&gt;", ">"), ("&lt;", "<")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip()


def listing_items(html):
    for block in ld_blocks(html):
        main = block.get("mainEntity") if isinstance(block, dict) else None
        if isinstance(main, dict) and "itemListElement" in main:
            return main["itemListElement"]
    raise SystemExit("Could not find the ItemList JSON-LD on the listing page.")


def detail(slug):
    url = f"{BASE}/resources/{slug}"
    try:
        html = get(url)
    except Exception as exc:  # network hiccup: keep the record, flag it
        return {"slug": slug, "error": str(exc)}

    description = ""
    vendor = ""
    for block in ld_blocks(html):
        if block.get("@type") == "WebPage":
            description = block.get("description") or ""
            vendor = (block.get("about") or {}).get("url") or ""

    if not re.match(r"^https?://", vendor or "", re.I):
        vendor = ""  # refuse javascript:, data: or relative targets

    body = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", "|", body)
    text = re.sub(r"\|+", "|", text)
    m = re.search(r"\|([^|]*)\|([^|]*)\|(Components|Icons|Motion &amp; 3D|Type &amp; Colour)\|", text)

    tagline = clean(m.group(1)) if m else ""
    full = clean(m.group(2)) if m else clean(description)
    if SUSPICIOUS.search(tagline + " " + full):
        return {"slug": slug, "flagged": "suspicious_text"}

    return {
        "slug": slug,
        "tagline": tagline,
        "description": full,
        "category": clean(m.group(3)) if m else "",
        "url": vendor,
    }


def build_catalog(rows):
    lines = [
        "# Resource catalog",
        "",
        f"All {len(rows)} destinations from [designeer.xyz/resources]({LISTING}), captured "
        f"{__import__('datetime').date.today().isoformat()}.",
        "Every entry links to the vendor site, not to the aggregator. Read a whole category when you need "
        "alternatives; otherwise use `scripts/search.py` to narrow first.",
        "",
    ]
    for cat in CATEGORIES:
        items = sorted((r for r in rows if r["category"] == cat), key=lambda r: r["name"].lower())
        lines += [f"## {cat} ({len(items)})", "", "| Resource | What it is | Link |", "|---|---|---|"]
        for r in items:
            tag = (r.get("tagline") or r.get("description") or "").replace("|", "\\|")
            if len(tag) > 150:
                tag = tag[:147].rstrip() + "…"
            name = r["name"].replace("|", "\\|")
            lines.append(f"| **{name}** | {tag} | <{r['url']}> |")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Refresh the design resource catalog.")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    existing = {}
    data_path = os.path.join(ROOT, "data", "resources.json")
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            existing = {r["slug"]: r for r in json.load(f)}

    print(f"Fetching {LISTING} ...", file=sys.stderr)
    items = listing_items(get(LISTING))
    print(f"Found {len(items)} resources.", file=sys.stderr)

    details = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(detail, it["url"].rstrip("/").split("/")[-1]): it for it in items
        }
        for n, fut in enumerate(as_completed(futures), 1):
            res = fut.result()
            details[res["slug"]] = res
            if "error" in res:
                print(f"  ! {res['slug']}: {res['error']}", file=sys.stderr)
            elif n % 25 == 0:
                print(f"  {n}/{len(items)}", file=sys.stderr)

    rows = []
    for it in items:
        slug = it["url"].rstrip("/").split("/")[-1]
        if slug in SKIP_SLUGS:
            print(f"  - skipping {it['name']} (not a design resource)", file=sys.stderr)
            continue
        d = details.get(slug, {})
        if d.get("flagged"):
            # Never overwrite vetted text with a page that looks injected.
            if slug in existing:
                print(f"  ! {it['name']}: {d['flagged']}, keeping cached text", file=sys.stderr)
                d = existing[slug]
            else:
                print(f"  - {it['name']}: {d['flagged']}, skipping", file=sys.stderr)
                continue
        elif not d.get("category"):
            # A transient fetch failure should not delete an entry we already have.
            if slug in existing:
                print(f"  ~ keeping cached {it['name']}", file=sys.stderr)
                d = existing[slug]
            else:
                # the source also lists non-design promo entries without a category
                print(f"  - skipping {it['name']} (no category)", file=sys.stderr)
                continue
        rows.append({
            "name": it["name"],
            "category": d["category"],
            "slug": slug,
            "tagline": d.get("tagline", ""),
            "description": d.get("description", ""),
            "url": d.get("url", ""),
            "source": it["url"],
        })

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "references"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "resources.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "data", "resources.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["name", "category", "tagline", "description", "url", "source"],
            extrasaction="ignore",
        )
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(ROOT, "references", "catalog.md"), "w", encoding="utf-8") as f:
        f.write(build_catalog(rows))

    print(f"Wrote {len(rows)} resources to data/ and references/catalog.md.", file=sys.stderr)


if __name__ == "__main__":
    main()

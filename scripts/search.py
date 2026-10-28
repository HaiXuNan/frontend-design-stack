#!/usr/bin/env python3
"""Search the frontend-design-stack resource catalog.

Stdlib only. Run from anywhere:

    python scripts/search.py "animated charts"
    python scripts/search.py "icon" --category Icons --limit 10
    python scripts/search.py --list-categories
    python scripts/search.py "font" --json
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, os.pardir, "data", "resources.json")

WEIGHTS = {"name": 6, "tagline": 3, "description": 1}

# Curated defaults by slug. They get a bounded boost so a broad query like
# "icon" surfaces Lucide before an arbitrary alphabetically early icon set,
# without overriding a precise query such as "evil charts".
PRIORITY = {
    "shadcn-ui": 1, "base-ui": 2, "radix": 3, "21st-dev": 4, "heroui": 5, "daisyui": 6,
    "headless-ui": 7, "tailark": 8, "motion-primitives": 9,
    "lucide": 1, "phosphor": 2, "iconify": 3, "simple-icons": 4, "tabler-icons": 5,
    "heroicons": 6, "lucide-animated": 7,
    "motion": 1, "gsap": 2, "rive": 3, "lottie": 4, "numberflow": 5, "three-js": 6,
    "react-three-fiber": 7,
    "fontshare": 1, "fontsource": 2, "utopia": 3, "oklch": 4, "apca": 5, "color-review": 6,
}

# Query terms are expanded so "animation" can reach "motion", "colour" can reach
# "color", and so on. The original term still drives the coverage bonus.
SYNONYMS = {
    "icon": ["icons"], "icons": ["icon"],
    "font": ["type", "typeface", "typography"], "fonts": ["type", "typography"],
    "typography": ["type", "font"], "typeface": ["type", "font"],
    "animation": ["motion", "animated", "animate"], "animated": ["motion", "animation"],
    "motion": ["animation", "animated"], "animate": ["motion", "animation"],
    "color": ["colour", "palette"], "colour": ["color", "palette"],
    "chart": ["charts", "graph", "visualization", "dashboard"],
    "charts": ["chart", "graph", "visualization", "dashboard"],
    "component": ["components"], "components": ["component"],
    "3d": ["three", "shader", "webgl"], "shader": ["shaders", "webgl", "3d"],
    "contrast": ["accessibility", "apca", "wcag"],
    "block": ["blocks", "section", "template"], "blocks": ["block", "section", "template"],
}

GENERIC_WORDS = {
    "icon", "icons", "component", "components", "library", "ui", "kit",
    "motion", "animation", "animated", "font", "fonts", "type", "typography",
    "color", "colour", "palette", "3d", "chart", "charts", "block", "blocks",
    "section", "sections", "landing", "page", "effect", "effects", "tool", "tools",
    "template", "templates", "gradient", "text",
}

# For a single generic word, only the matching category is worth returning;
# otherwise "charts" drifts into animation libraries that mention charts once.
CATEGORY_HINTS = {
    "icon": ["Icons"], "icons": ["Icons"],
    "component": ["Components"], "components": ["Components"],
    "library": ["Components"], "ui": ["Components"], "kit": ["Components"],
    "block": ["Components"], "blocks": ["Components"], "section": ["Components"],
    "sections": ["Components"], "landing": ["Components"], "page": ["Components"],
    "template": ["Components"], "templates": ["Components"],
    "chart": ["Components"], "charts": ["Components"],
    "motion": ["Motion & 3D"], "animation": ["Motion & 3D"], "animated": ["Motion & 3D"],
    "3d": ["Motion & 3D"],
    "font": ["Type & Colour"], "fonts": ["Type & Colour"], "type": ["Type & Colour"],
    "typography": ["Type & Colour"], "color": ["Type & Colour"], "colour": ["Type & Colour"],
    "palette": ["Type & Colour"],
}

FIELD_TIER = {"name": 0, "tagline": 1, "description": 2}


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def term_hit(item, term):
    """Best weighted hit for one term across fields (0 if absent).

    Matching starts at a word boundary but allows prefixes, so "chart" finds
    "charts" while "graph" does not match inside "typography".
    """
    pattern = re.compile(r"(?<![a-z0-9])" + re.escape(term))
    best = 0
    for field, weight in WEIGHTS.items():
        value = (item.get(field) or "").lower()
        m = pattern.search(value)
        if m:
            # whole-word and leading matches are stronger than mid-sentence ones
            if value == term:
                hit = weight * 3
            elif m.start() == 0:
                hit = weight * 2
            else:
                hit = weight
            best = max(best, hit)
    return best


def term_tier(item, term):
    """Best (most prominent) field in which a term appears."""
    pattern = re.compile(r"(?<![a-z0-9])" + re.escape(term))
    tier = 9
    for field, rank in FIELD_TIER.items():
        if pattern.search((item.get(field) or "").lower()):
            tier = min(tier, rank)
    return tier


def evaluate(item, terms):
    """Return (score, relevance_tier, matched_terms) or None."""
    total = 0
    matched = 0
    tier = 9
    for term in terms:
        variants = [term] + SYNONYMS.get(term, [])
        hit = max(term_hit(item, v) for v in variants)
        if hit:
            matched += 1
            total += hit
            tier = min(tier, min(term_tier(item, v) for v in variants))
    if not matched:
        return None
    # reward results that cover more of the query, so "font pairing" prefers
    # items about both fonts and pairing over items about only one
    return total + matched * 5, tier, matched


def main():
    ap = argparse.ArgumentParser(description="Search curated front-end design resources.")
    ap.add_argument("query", nargs="*", help="search terms; results covering more terms rank higher")
    ap.add_argument("--category", help="filter by category, e.g. Icons")
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--list-categories", action="store_true")
    args = ap.parse_args()

    items = load()
    categories = sorted({i["category"] for i in items if i.get("category")})

    if args.list_categories:
        for c in categories:
            print(f"{c}: {sum(1 for i in items if i['category'] == c)}")
        return

    if not args.query:
        ap.error("provide search terms, or use --list-categories")

    if args.category:
        wanted = args.category.lower()
        items = [i for i in items if wanted in (i.get("category") or "").lower()]
        if not items:
            print(f"No resources in category '{args.category}'. Try: {', '.join(categories)}", file=sys.stderr)
            sys.exit(1)

    # Accept both `search.py animated charts` and `search.py "animated charts"`.
    terms = [word for chunk in args.query for word in chunk.lower().split()]
    singular = terms[0] if len(terms) == 1 else None
    if singular in CATEGORY_HINTS:
        allowed = CATEGORY_HINTS[singular]
        items = [i for i in items if i.get("category") in allowed]

    ranked = []
    for item in items:
        ev = evaluate(item, terms)
        if ev:
            ranked.append((ev, item))

    # A query made only of generic category words ("icon", "component library",
    # "animation") should lead with curated defaults, not with whichever name
    # happens to contain the word first. For specific queries, relevance tier
    # (name > category > tagline > description) leads and priority only breaks ties.
    generic = all(t in GENERIC_WORDS for t in terms)
    if generic and len(terms) == 1:
        ranked.sort(key=lambda p: (
            0 if p[1].get("slug") in PRIORITY else 1,
            PRIORITY.get(p[1].get("slug"), 0),
            p[0][1],
            -p[0][0],
            p[1]["name"].lower(),
        ))
    else:
        ranked.sort(key=lambda p: (
            -p[0][2],  # a result covering more query terms wins
            p[0][1],
            0 if p[1].get("slug") in PRIORITY else 1,
            PRIORITY.get(p[1].get("slug"), 0),
            -p[0][0],
            p[1]["name"].lower(),
        ))

    if not ranked:
        print("No match. Broaden the query or check --list-categories.", file=sys.stderr)
        sys.exit(1)

    results = [item for _, item in ranked[: args.limit]]

    if len(terms) > 1 and ranked[0][0][2] < len(terms):
        print(
            f"Note: no resource matches all {len(terms)} terms; showing the closest "
            f"({ranked[0][0][2]} of {len(terms)}).\n",
            file=sys.stderr,
        )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for n, item in enumerate(results, 1):
        print(f"{n}. {item['name']}  [{item['category']}]")
        print(f"   {item.get('tagline') or item.get('description', '')[:160]}")
        print(f"   {item['url']}")
    if len(ranked) > len(results):
        print(f"\n{len(ranked) - len(results)} more match; raise --limit or read references/catalog.md.")


if __name__ == "__main__":
    main()

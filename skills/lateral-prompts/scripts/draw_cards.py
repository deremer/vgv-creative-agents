#!/usr/bin/env python3
"""Draw cards for a lateral-prompts session.

Picks 2 random cards from the Canonical Deck and 2 unique random categories.
Done in Python rather than letting the LLM pick because the lateral pull only
works if the choice is genuinely uncorrelated with the focus area — an LLM
choosing "randomly" tends to pick cards that already feel relevant, which
defeats the purpose.

Usage:
    draw_cards.py [--seed N] [--canonical PATH]

Output: JSON to stdout with `drawn_cards`, `ephemeral_categories`, `deck_size`.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

CATEGORIES = [
    "Strategy",
    "Gnomic",
    "Permission",
    "Body",
    "Maker psychology",
    "Tactical",
    "Koan",
]

# Workflow contract: each session draws 2 canonical cards (random from the
# deck) plus 2 ephemeral cards (one per category, categories sampled here).
# Changing either constant breaks the orchestrator's Step 5 fan-out.
NUM_CANONICAL_DRAWS = 2
NUM_EPHEMERAL_CATEGORIES = 2


def default_canonical_path() -> Path:
    # scripts/draw_cards.py -> ../references/lateral-prompts.md (skill root)
    return Path(__file__).resolve().parents[1] / "references" / "lateral-prompts.md"


def parse_canonical_deck(text: str) -> list[str]:
    match = re.search(r"##\s+Canonical Deck\s*\n(.+?)(?=\n##\s|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError("Could not find '## Canonical Deck' section")

    cards: list[str] = []
    for line in match.group(1).splitlines():
        m = re.match(r"^\s*\d+\.\s+(.+?)\s*$", line)
        if m:
            cards.append(m.group(1))
    return cards


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducibility")
    parser.add_argument(
        "--canonical",
        type=Path,
        default=None,
        help="Path to lateral-prompts.md (default: plugin reference/)",
    )
    args = parser.parse_args()

    canonical_path = args.canonical or default_canonical_path()
    if not canonical_path.exists():
        print(f"Canonical deck not found at: {canonical_path}", file=sys.stderr)
        return 1

    deck = parse_canonical_deck(canonical_path.read_text(encoding="utf-8"))
    if len(deck) < NUM_CANONICAL_DRAWS:
        print(f"Canonical deck too small: {len(deck)} cards", file=sys.stderr)
        return 1

    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    drawn_cards = rng.sample(deck, NUM_CANONICAL_DRAWS)
    ephemeral_categories = rng.sample(CATEGORIES, NUM_EPHEMERAL_CATEGORIES)

    result = {
        "drawn_cards": drawn_cards,
        "ephemeral_categories": ephemeral_categories,
        "deck_size": len(deck),
        "canonical_path": str(canonical_path),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

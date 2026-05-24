#!/usr/bin/env python3
"""
Poker equity calculator — hand or range vs villain's range.

Examples
--------
# Specific hand vs a 3-bet range (preflop)
python3 equity.py --hero TT --villain "QQ+,AKs,AKo"

# Hand vs range on a flop
python3 equity.py --hero TT --villain "QQ+,AKs,AKo" --board "Ah,7c,2d"

# Full range vs range (range advantage)
python3 equity.py --hero "TT,99,AKs,AQs" --villain "QQ+,AKs,AKo" --board "Th,7c,2d"

# Show equity for every combo in hero's range
python3 equity.py --hero "TT,99,AKs" --villain "QQ+,AKs,AKo" --board "Th,7c,2d" --detail

Range notation:
  TT        pair  |  AKs suited  |  AKo offsuit  |  AK both
  QQ+       QQ, KK, AA           |  ATs+  ATs through AKs
  QQ+,AKs,JTs  comma-separated mix

Board: Ah,7c,2d  (with or without commas)
Cards: rank (2-9 T J Q K A) + suit (c d h s)
"""

import argparse
import sys
import eval7


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_board(s: str) -> list:
    s = s.replace(",", "").replace(" ", "")
    if not s:
        return []
    if len(s) % 2 != 0:
        raise ValueError(f"Bad board string: {s!r}")
    return [eval7.Card(s[i:i+2]) for i in range(0, len(s), 2)]


# ── Equity ────────────────────────────────────────────────────────────────────

def calc_equity(hero_range_str: str, villain_range_str: str,
                board: list, samples: int = 20000) -> dict:
    """
    Return {hand_str: equity_float} for every combo in hero's range.
    eval7 handles dead-card filtering internally.
    """
    hero_range    = eval7.HandRange(hero_range_str)
    villain_range = eval7.HandRange(villain_range_str)

    # py_all_hands_vs_range returns {(c1,c2): equity}
    raw = eval7.py_all_hands_vs_range(hero_range, villain_range, board, samples)

    results = {}
    for (c1, c2), eq in raw.items():
        results[f"{c1}{c2}"] = eq
    return results


# ── Formatting ────────────────────────────────────────────────────────────────

def pct(f: float) -> str:
    return f"{f * 100:.1f}%"


def print_results(hero_range: str, villain_range: str, board: list,
                  equities: dict, detail: bool):
    board_str = " ".join(str(c) for c in board) if board else "(preflop)"
    vals = list(equities.values())
    avg  = sum(vals) / len(vals) if vals else 0.5

    print(f"\nBoard  : {board_str}")
    print(f"Hero   : {hero_range}")
    print(f"Villain: {villain_range}")
    print(f"Combos : {len(vals)}")
    print()
    print(f"  Hero avg equity    : {pct(avg)}")
    print(f"  Villain avg equity : {pct(1 - avg)}")

    adv = avg - 0.5
    if abs(adv) < 0.005:
        print("  Range advantage    : roughly even")
    elif adv > 0:
        print(f"  Range advantage    : Hero +{pct(adv)}")
    else:
        print(f"  Range advantage    : Villain +{pct(-adv)}")

    if vals:
        best_hand  = max(equities, key=equities.get)
        worst_hand = min(equities, key=equities.get)
        print()
        print(f"  Best  : {best_hand}  {pct(equities[best_hand])}")
        print(f"  Worst : {worst_hand}  {pct(equities[worst_hand])}")

    if detail and equities:
        print()
        print("  Per-combo breakdown (sorted by equity):")
        for hand, eq in sorted(equities.items(), key=lambda x: -x[1]):
            filled = int(eq * 28)
            bar = "█" * filled + "░" * (28 - filled)
            print(f"    {hand}  {bar}  {pct(eq)}")

    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Poker equity: hand/range vs villain range",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--hero",    "-H", required=True,
                        help="Hero hand (TT) or range (TT,AKs,QQ+)")
    parser.add_argument("--villain", "-V", required=True,
                        help="Villain range (e.g. QQ+,AKs,AKo)")
    parser.add_argument("--board",   "-b", default="",
                        help="Board cards e.g. Ah,7c,2d  (omit for preflop)")
    parser.add_argument("--detail",  "-d", action="store_true",
                        help="Show equity per combo")
    parser.add_argument("--samples", "-s", type=int, default=20000,
                        help="Monte Carlo samples (default 20000)")
    args = parser.parse_args()

    board    = parse_board(args.board)
    equities = calc_equity(args.hero, args.villain, board, args.samples)

    if not equities:
        print("No valid hero combos found (check for card conflicts with board).")
        sys.exit(1)

    print_results(args.hero, args.villain, board, equities, args.detail)


if __name__ == "__main__":
    main()

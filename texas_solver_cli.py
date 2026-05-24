#!/usr/bin/env python3
"""
Thin CLI wrapper for TexasSolver — heads-up postflop GTO solver.

Usage (direct):
  echo '{...}' | python3 texas_solver_cli.py

Usage (from file):
  python3 texas_solver_cli.py --input hand.json --output result.json

JSON input schema:
  pot             int     pot size in chips
  stack           int     effective stack in chips
  board           str     e.g. "Qs,8d,7h" or "Qs,8d,7h,2c" or "Qs,8d,7h,2c,Kd"
  range_ip        str     IP range in TexasSolver format
  range_oop       str     OOP range in TexasSolver format
  bet_sizes       dict    key pattern: "{pos}_{street}_{type}" -> "{size}[,{size}]"
                          pos: oop|ip  street: flop|turn|river  type: bet|raise|donk|allin
  allin_threshold float   default 1.0 (fraction of pot)
  threads         int     default 8
  iterations      int     default 200
  accuracy        float   default 0.5
  game_mode       str     "holdem" (default) or "shortdeck"
  locked_nodes    list    node-path locks (see below)
  locked_streets  list    bulk-street locks (see below)

Node locking — model a specific player's tendencies instead of using GTO:

  locked_nodes: list of {
    "path":   "<step>[:<step>…]"   action path from root using b<amt>, r<amt>, c, k, f
    "player": "ip" | "oop"
    "freqs":  {"fold": 0.7, "call": 0.3, "raise": 0.0}   (normalised automatically)
  }

  locked_streets: list of {
    "street": "flop" | "turn" | "river"
    "player": "ip" | "oop"
    "facing": "bet" | "check" | "any"    (which nodes to lock on that street)
    "freqs":  {"fold": 0.7, "call": 0.3}
  }

  Path notation:
    b<n>  bet/raise to n chips total  (e.g. b2 = 2-chip bet)
    r<n>  raise to n chips total
    c     call or check
    k     check (disambiguates from call)
    f     fold

JSON output:
  The full TexasSolver result JSON, with an added "solver_log" field.
  Locked nodes show the specified frequencies; the opponent's strategy
  is the exact exploit against that fixed behaviour.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SOLVER_DIR = Path(__file__).parent / "texas_solver"
SOLVER_BIN = SOLVER_DIR / "console_solver"

DEFAULT_BET_SIZES = {
    "oop_flop_bet": "50",
    "oop_flop_raise": "60",
    "oop_flop_allin": None,
    "ip_flop_bet": "50",
    "ip_flop_raise": "60",
    "ip_flop_allin": None,
    "oop_turn_bet": "50",
    "oop_turn_raise": "60",
    "oop_turn_allin": None,
    "ip_turn_bet": "50",
    "ip_turn_raise": "60",
    "ip_turn_allin": None,
    "oop_river_bet": "50",
    "oop_river_donk": "50",
    "oop_river_raise": "60",
    "oop_river_allin": None,
    "ip_river_bet": "50",
    "ip_river_raise": "60",
    "ip_river_allin": None,
}


def build_input_file(params: dict) -> str:
    lines = []
    lines.append(f"set_pot {params['pot']}")
    lines.append(f"set_effective_stack {params['stack']}")
    lines.append(f"set_board {params['board']}")
    lines.append(f"set_range_ip {params['range_ip']}")
    lines.append(f"set_range_oop {params['range_oop']}")

    bet_sizes = {**DEFAULT_BET_SIZES, **params.get("bet_sizes", {})}
    for key, val in bet_sizes.items():
        parts = key.split("_", 2)  # pos, street, type
        if len(parts) != 3:
            continue
        pos, street, bet_type = parts
        if val is None:
            lines.append(f"set_bet_sizes {pos},{street},{bet_type}")
        else:
            lines.append(f"set_bet_sizes {pos},{street},{bet_type},{val}")

    threshold = params.get("allin_threshold", 1.0)
    lines.append(f"set_allin_threshold {threshold}")
    lines.append("build_tree")

    # Node locking — must come after build_tree, before start_solve
    for lock in params.get("locked_nodes", []):
        freqs_str = ",".join(f"{k}={v}" for k, v in lock["freqs"].items())
        lines.append(f"lock_node {lock['path']} {lock['player']} {freqs_str}")

    for lock in params.get("locked_streets", []):
        freqs_str = ",".join(f"{k}={v}" for k, v in lock["freqs"].items())
        lines.append(
            f"lock_all_street {lock['street']} {lock['player']} {lock.get('facing','any')} {freqs_str}"
        )

    lines.append(f"set_thread_num {params.get('threads', 8)}")
    lines.append(f"set_accuracy {params.get('accuracy', 0.5)}")
    lines.append(f"set_max_iteration {params.get('iterations', 200)}")
    lines.append("set_print_interval 10")
    lines.append("set_use_isomorphism 1")
    lines.append("start_solve")
    lines.append("set_dump_rounds 2")
    return "\n".join(lines)


def solve(params: dict) -> dict:
    if not SOLVER_BIN.exists():
        raise FileNotFoundError(f"Solver binary not found at {SOLVER_BIN}")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.txt"
        output_path = Path(tmpdir) / "output.json"

        input_path.write_text(build_input_file(params))

        # dump_result path must be relative to where the solver runs, or absolute
        with open(input_path, "a") as f:
            f.write(f"\ndump_result {output_path}")

        result = subprocess.run(
            [str(SOLVER_BIN), "-i", str(input_path),
             "-r", str(SOLVER_DIR / "resources"),
             "-m", params.get("game_mode", "holdem")],
            capture_output=True, text=True, cwd=tmpdir
        )

        solver_log = result.stdout + result.stderr
        if result.returncode != 0:
            raise RuntimeError(f"Solver failed:\n{solver_log}")

        if not output_path.exists():
            raise RuntimeError(f"Solver ran but no output JSON produced.\nLog:\n{solver_log}")

        with open(output_path) as f:
            output = json.load(f)

        output["solver_log"] = solver_log
        return output


def main():
    parser = argparse.ArgumentParser(description="TexasSolver JSON wrapper")
    parser.add_argument("--input", "-i", help="JSON input file (default: stdin)")
    parser.add_argument("--output", "-o", help="JSON output file (default: stdout)")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            params = json.load(f)
    else:
        params = json.load(sys.stdin)

    result = solve(params)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    else:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()

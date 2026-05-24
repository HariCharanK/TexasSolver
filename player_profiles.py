"""
Pre-built node-locking profiles for common player stereotypes.

Each profile returns a dict of locked_nodes / locked_streets that can be
merged directly into a texas_solver_cli.py params dict.

Usage:
    from player_profiles import profile_calling_station
    params = {
        "pot": 4, "stack": 10, "board": "Qs,8d,7h",
        "range_ip": "T9s", "range_oop": "JTs,43s",
        **profile_calling_station("ip"),   # model IP as a calling station
    }

All profiles operate on one player ("ip" or "oop") and return:
  {
    "locked_streets": [...],
    "locked_nodes":   [...],   # usually empty; populated only for path-specific locks
  }

Available profiles
------------------
profile_calling_station         – calls too often, rarely folds
profile_loose_preflop_tight_postflop – wide range pre, folds to C-bets post
profile_turn_bomber             – traps flop, bombs turn after check-through
profile_passive_fish            – never bets/raises, only calls and checks
profile_manic_whale             – bets and raises constantly, never folds
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _street_lock(street, player, facing, freqs):
    return {"street": street, "player": player, "facing": facing, "freqs": freqs}


def _node_lock(path, player, freqs):
    return {"path": path, "player": player, "freqs": freqs}


# ── Profiles ──────────────────────────────────────────────────────────────────

def profile_calling_station(player: str) -> dict:
    """
    Calling station: calls way too often facing bets/raises, almost never folds.
    Implies: value-bet wider and thinner; reduce bluffs.
    """
    return {
        "locked_streets": [
            _street_lock("flop",  player, "bet",   {"fold": 0.05, "call": 0.90, "raise": 0.05}),
            _street_lock("flop",  player, "raise", {"fold": 0.05, "call": 0.90, "raise": 0.05}),
            _street_lock("turn",  player, "bet",   {"fold": 0.08, "call": 0.88, "raise": 0.04}),
            _street_lock("turn",  player, "raise", {"fold": 0.08, "call": 0.88, "raise": 0.04}),
            _street_lock("river", player, "bet",   {"fold": 0.10, "call": 0.88, "raise": 0.02}),
            _street_lock("river", player, "raise", {"fold": 0.10, "call": 0.88, "raise": 0.02}),
        ],
        "locked_nodes": [],
    }


def profile_loose_preflop_tight_postflop(player: str) -> dict:
    """
    Wide range pre-flop but folds too often to C-bets post-flop.
    Implies: C-bet more often (even thin); bluff more on dry boards.
    """
    return {
        "locked_streets": [
            _street_lock("flop",  player, "bet",   {"fold": 0.55, "call": 0.38, "raise": 0.07}),
            _street_lock("turn",  player, "bet",   {"fold": 0.52, "call": 0.40, "raise": 0.08}),
            _street_lock("river", player, "bet",   {"fold": 0.50, "call": 0.44, "raise": 0.06}),
        ],
        "locked_nodes": [],
    }


def profile_turn_bomber(player: str) -> dict:
    """
    Checks flop with everything (trapping), then bombs turn after check-through.
    Implies: protect your flop checking range; call turn bets wider.
    """
    return {
        "locked_streets": [
            # Flop: check everything (passive, trapping)
            _street_lock("flop", player, "check", {"check": 1.0, "bet": 0.0}),
            # Turn after check-check: massive bet frequency
            _street_lock("turn", player, "check", {"check": 0.1, "bet": 0.9}),
        ],
        "locked_nodes": [],
    }


def profile_passive_fish(player: str) -> dict:
    """
    Passive recreational player: never bets/raises, only calls and checks.
    Implies: value-bet every street; triple-barrel mercilessly.
    """
    return {
        "locked_streets": [
            _street_lock("flop",  player, "check", {"check": 0.95, "bet": 0.05}),
            _street_lock("flop",  player, "bet",   {"fold": 0.10, "call": 0.88, "raise": 0.02}),
            _street_lock("flop",  player, "raise", {"fold": 0.10, "call": 0.88, "raise": 0.02}),
            _street_lock("turn",  player, "check", {"check": 0.95, "bet": 0.05}),
            _street_lock("turn",  player, "bet",   {"fold": 0.12, "call": 0.86, "raise": 0.02}),
            _street_lock("turn",  player, "raise", {"fold": 0.12, "call": 0.86, "raise": 0.02}),
            _street_lock("river", player, "check", {"check": 0.98, "bet": 0.02}),
            _street_lock("river", player, "bet",   {"fold": 0.15, "call": 0.83, "raise": 0.02}),
            _street_lock("river", player, "raise", {"fold": 0.15, "call": 0.83, "raise": 0.02}),
        ],
        "locked_nodes": [],
    }


def profile_manic_whale(player: str) -> dict:
    """
    Manic / whale: bets and raises constantly, never folds.
    Implies: trap heavily; check strong hands to let them bet; thin-value less.
    """
    return {
        "locked_streets": [
            # Manic opens betting constantly
            _street_lock("flop",  player, "check", {"check": 0.10, "bet": 0.90}),
            _street_lock("turn",  player, "check", {"check": 0.10, "bet": 0.90}),
            _street_lock("river", player, "check", {"check": 0.05, "bet": 0.95}),
            # And almost never folds to aggression
            _street_lock("flop",  player, "bet",   {"fold": 0.02, "call": 0.58, "raise": 0.40}),
            _street_lock("flop",  player, "raise", {"fold": 0.02, "call": 0.58, "raise": 0.40}),
            _street_lock("turn",  player, "bet",   {"fold": 0.03, "call": 0.57, "raise": 0.40}),
            _street_lock("turn",  player, "raise", {"fold": 0.03, "call": 0.57, "raise": 0.40}),
            _street_lock("river", player, "bet",   {"fold": 0.05, "call": 0.70, "raise": 0.25}),
            _street_lock("river", player, "raise", {"fold": 0.05, "call": 0.70, "raise": 0.25}),
        ],
        "locked_nodes": [],
    }


if __name__ == "__main__":
    import json
    print("=== Calling station (IP) ===")
    print(json.dumps(profile_calling_station("ip"), indent=2))
    print("\n=== Loose-pre / tight-post (OOP) ===")
    print(json.dumps(profile_loose_preflop_tight_postflop("oop"), indent=2))
    print("\n=== Turn bomber (IP) ===")
    print(json.dumps(profile_turn_bomber("ip"), indent=2))

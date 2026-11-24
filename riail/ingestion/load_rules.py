"""Ingestion script: reads the rule files and loads them into the RuleStore.

Simplified in D1 section 1.4: a one-off script instead of a pipeline, and
rules are checked by hand before they go in the data folder (admin review
is Deferred).

Run with:  python -m riail.ingestion.load_rules

Each file in data/rules/ holds one rule set. A file with a "base" (the trial
rules) is laid on top of that base: a trial rule with the same number
replaces the base rule, and new numbers are added. So the trial rule set
holds the full rulebook a college referee needs, not just the changes.
"""

import json
from datetime import date
from pathlib import Path

from riail.models import RuleChunk, RuleSet
from riail.rulestore.interface import RuleStore


class RuleFileError(ValueError):
    """A rule file is missing something or has a value the app cannot use."""


def read_rule_file(path: Path) -> dict:
    """Read and check one rule file. Returns its rule set, base and RuleChunks."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RuleFileError(f"{path.name}: not valid JSON ({e})") from e

    for key in ("rule_set", "source", "effective_from", "rules"):
        if key not in data:
            raise RuleFileError(f"{path.name}: missing '{key}'")
    try:
        rule_set = RuleSet(data["rule_set"])
        base = RuleSet(data["base"]) if data.get("base") else None
    except ValueError as e:
        raise RuleFileError(f"{path.name}: {e}") from e

    chunks, seen = [], set()
    for i, rule in enumerate(data["rules"], start=1):
        try:
            chunk = RuleChunk(
                rule_number=str(rule["rule_number"]),
                rule_set=rule_set,
                title=rule.get("title", ""),
                text=rule["text"],
                effective_from=date.fromisoformat(rule.get("effective_from", data["effective_from"])),
                source=rule.get("source", data["source"]),
            )
        except (KeyError, ValueError) as e:
            raise RuleFileError(f"{path.name}, rule {i}: {e}") from e
        if chunk.rule_number in seen:
            raise RuleFileError(f"{path.name}: rule {chunk.rule_number} appears twice")
        seen.add(chunk.rule_number)
        chunks.append(chunk)

    return {"rule_set": rule_set, "base": base, "chunks": chunks}


def build_rule_sets(data_dir: Path) -> list[RuleChunk]:
    """Read every rule file and return all chunks, with overlays applied."""
    files = sorted(Path(data_dir).glob("*.json"))
    if not files:
        raise RuleFileError(f"No rule files found in {data_dir}")
    parsed = {}
    for f in files:
        info = read_rule_file(f)
        if info["rule_set"] in parsed:
            raise RuleFileError(f"Rule set {info['rule_set'].value} is defined twice")
        parsed[info["rule_set"]] = info

    all_chunks = []
    for rule_set, info in parsed.items():
        chunks = list(info["chunks"])
        if info["base"] is not None:
            if info["base"] not in parsed:
                raise RuleFileError(f"{rule_set.value} is based on {info['base'].value}, which was not found")
            overridden = {c.rule_number for c in chunks}
            for base_chunk in parsed[info["base"]]["chunks"]:
                if base_chunk.rule_number not in overridden:
                    # Copy the base rule into this rule set, so a search of this set finds it.
                    chunks.append(RuleChunk(
                        rule_number=base_chunk.rule_number,
                        rule_set=rule_set,
                        title=base_chunk.title,
                        text=base_chunk.text,
                        effective_from=base_chunk.effective_from,
                        source=base_chunk.source,
                    ))
        all_chunks.extend(chunks)
    return all_chunks


def load(store: RuleStore, data_dir: Path) -> dict[RuleSet, int]:
    """Replace everything in the store with the rules in data_dir. Returns counts per rule set."""
    chunks = build_rule_sets(data_dir)  # read and check everything before touching the store
    store.clear()
    store.add(chunks)
    return {rs: store.count(rs) for rs in RuleSet}


def main():
    from riail.config import Config
    from riail.wiring import build_rule_store

    config = Config.from_env()
    counts = load(build_rule_store(config), Path(config.rules_dir))
    for rule_set, n in counts.items():
        print(f"Loaded {n} rules for {rule_set.label}")


if __name__ == "__main__":
    main()

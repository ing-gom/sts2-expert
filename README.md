# STS2 Expert — Card/Relic/Potion Evaluation Agent & Catalog

**English** · [한국어](README.ko.md)

A public bundle containing a **Claude Code expert agent that catalogs and evaluates the
cards, relics, and potions** of Slay the Spire 2 (Early Access), the data snapshots the
agent relies on, and a browser-based HTML catalog viewer.

**📊 Catalog viewer**: https://ing-gom.github.io/sts2-expert/
— Every card, relic, and potion shows an **S–D grade badge**, with grade sorting, grade
filtering, and a one-line rationale.

## Layout

```
.claude/agents/sts2-expert.md     # Evaluation expert agent (read-only evaluator)
.claude/skills/
  tier-judge/                     # Per-cost efficiency table + grading rubric
  card-expected-value/            # 5-turn EV (Expected Value) measurement basis
  card-effect-verify/             # Close-reading verification procedure for descriptions
eval_criteria.md                  # Evaluation criteria (efficiency, scaling, new mechanics, character meta)
data/                             # Game data snapshots (from headless dumps)
index.html                        # Catalog viewer (GitHub Pages)
```

## Using the agent

With [Claude Code](https://claude.com/claude-code) installed:

```bash
git clone https://github.com/ing-gom/sts2-expert
cd sts2-expert
claude
```

Opening Claude Code inside the repo auto-registers the `sts2-expert` agent. Examples:

```
"Evaluate BLOOD_POTION with the sts2-expert agent"
"Catalog and grade all Silent rare cards"
"How good is the Akabeko relic?"
```

## Evaluation principles

The agent is a **read-only evaluator** — it organizes information from the data and returns
reports with S–D grades and rationale; it never modifies files.

- **Standalone judgment**: Grades are derived solely from a card's **factual effects** and the
  **rubric** in `eval_criteria.md`. External evaluation data such as community tier lists
  (`tier`/`score` fields, external tier CSVs) has been **removed from the bundle** and is never
  consulted or cited at any stage. (The empirical causal data in `card_empirical_lift.json` is a
  *measurement*, not an *external opinion*, so it may be cited.)
- **Static vs. contextual separation**: Static grades (ceiling) and contextual grades
  (deck/timing) are always evaluated separately.
- **Criteria upkeep**: `eval_criteria.md` holds the efficiency tables, scaling, deck-thinning,
  new mechanics (Corrosion/Penetration/Durability), conditional penalties, and character-meta
  criteria — it captures evaluation **methodology and meta**, not tier **values**.

The grades published in the viewer are this agent's standalone evaluation results
(`data/grades.json`).

## Data

| File | Contents |
|---|---|
| `data/cards_catalog.json` | Card master catalog (1,117 incl. upgrades, `game_version` v0.103.2 — `tier`/`score` fields removed) |
| `data/grades.json` | **Agent standalone S–D grades** (577 cards · 309 relics · 64 potions; grade + context + one-line rationale; optional per-upgrade grade) |
| `data/card_expected_value.json` | Card EV — 5-turn baseline damage equivalent |
| `data/card_axis_overrides.json` | Explicit axis tags (Producer/Consumer/Amplifier/Trigger) |
| `data/card_empirical_lift.json` | Full-run measured causal card lift (not an external opinion) |
| `data/role_needs.json` | Cross-axis synergy direction/weights |
| `data/build_completion.json` | Per-character/archetype keystone definitions |
| `data/effect_value_table.json` | Value-conversion table by effect type |
| `data/axis_labels_ko.json` | Korean axis labels |
| `data/relics_locale.json` | 309 relics, ko/en/zh names + descriptions (`game_version` v0.103.3) |
| `data/relic_canonical_vars.json` | Relic placeholder real values (constants extracted from the game DLL) |
| `data/relic_axis_overrides.json` | Relic → card axis synergy mapping |
| `data/potions.json` | 64 potions — ko/en/zh names/descriptions + Rarity/Usage/Target + **placeholder real values** (headless dump) + curated classification (`game_version` v0.103.3) |

> Dump versions differ by component — cards are the stable v0.103.2 snapshot; relics and potions are v0.103.3.

## Running the viewer locally

`index.html` fetches `data/*.json`, so it cannot be opened via `file://`:

```bash
python -m http.server 8000
# http://localhost:8000
```

## License / notice

An unofficial fan project. Rights to the game data belong to Mega Crit.
Given Early Access, data snapshots may differ from the latest game balance.
The tooling code (agent/skills/viewer) is under the MIT license.

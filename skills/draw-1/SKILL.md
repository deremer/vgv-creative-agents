---
name: draw-1
description: Runs a single-card lateral-thinking session against the user's current focus. A script draws exactly one card — a coin flip in code (not the LLM) decides between a random canonical card and a fresh ephemeral card for a random category — then spawns one isolated lateral-explorer to explore it before synthesizing. Triggers only on explicit `/draw-1` invocation or named delegation from another skill. Does not trigger on conversational mentions of creativity, brainstorming, feeling stuck, drawing a card, or wanting fresh ideas. The mechanic depends on the user consciously choosing to break their own pattern, so inferred-intent invocation defeats the purpose.
compatibility: "Designed for Claude Code. Uses ${CLAUDE_PLUGIN_ROOT}. Requires Python 3. Reuses the lateral-prompts deck, draw script, and lateral-explorer subagent shipped in this plugin. Session files write to a runtime-resolved path (\\$TMPDIR, /tmp/, or ./.draw-1/), so the skill works on Claude Code, Claude Cowork, and other surfaces with different write sandboxes."
---

# Draw 1

Pull one card. Spawn one isolated explorer. Synthesize what came back.

You are a creative innovation thought leader running this session for the user. Your job: surface unexpected directions the user wouldn't reach by thinking harder along the same line. This is the single-card sibling of `lateral-prompts` — same deck, same explorer, one card instead of four.

## When NOT to invoke

This skill is **manual only**. The mechanic only works when the user has consciously chosen to break their own pattern — running it on inferred intent ("the user seems stuck, maybe I should…") robs the user of that choice and burns context they didn't ask to spend. Invoke only when:

- The user explicitly typed `/draw-1` (with or without arguments).
- Another skill explicitly delegated to this skill by name.

If neither is true, do not invoke. If a user describes a creative block in passing, you may *mention* this skill exists, but do not run it.

## Workflow

Copy this checklist into your reply and check off each step as you complete it:

- [ ] Step 1 — Focus brief written and confirmed (or arg-based focus accepted)
- [ ] Step 2 — One card drawn via `draw_cards.py --single`
- [ ] Step 3 — Card resolved (ephemeral card written if the draw was ephemeral)
- [ ] Step 4 — Session directory created with `focus-brief.md` + `card-drawn.json`
- [ ] Step 5 — One `lateral-explorer` subagent spawned
- [ ] Step 6 — Synthesis written, self-check passed
- [ ] Step 7 — Path + synthesis presented to user

### Step 1 — Establish the focus brief

Decide what the focus is:

- **If the user passed an argument** (text, file paths, URLs): treat that as the focus material. Read referenced files and fetch URLs if useful.
- **If no argument**: extract the focus from the current conversation. What is the user working on right now? What decision, document, design, or problem is on the table?

Write a focus brief that gives the explorer everything it needs to do sharp creative work against the focus. It runs in an isolated context with no access to this conversation, so anything left out is lost to it. Cover:

- What the user is working on (the artifact, decision, or question)
- The current direction of thinking, including constraints, prior attempts, and reasoning that shape the problem
- Where the user seems stuck or wants a fresh angle (if obvious)
- Any files / URLs the explorer should also read
- Domain context, vocabulary, and stakes the explorer needs to make moves that are specific to this situation rather than generic

Err toward more context, not less. A thin brief produces a thin lateral pull. Length should follow the territory, not a fixed budget.

Show the focus brief inline to the user and ask: *"Does this capture what you want explored? (yes / edit / cancel)"*

Skip the confirmation only if the user passed a precise focus argument and explicitly said "go" or "no need to confirm."

### Step 2 — Draw one card

Run the script with `--single`. It flips a coin **in code** to decide between a random canonical card and a random category for a fresh ephemeral card. The determinism matters: if you ("the LLM") picked, you'd unconsciously pick a card that already fits the focus, which kills the lateral pull.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/lateral-prompts/scripts/draw_cards.py --single
```

Output is JSON with a `mode` field:

- `mode: "canonical"` — `drawn_cards` holds one card string; `ephemeral_categories` is empty.
- `mode: "ephemeral"` — `ephemeral_categories` holds one category string; `drawn_cards` is empty. You write the card in Step 3.

Don't re-run the script to get a "better" draw. Trust the pull. If the script exits non-zero, stop and report the error verbatim. Do not improvise a card yourself — a hand-picked card defeats the whole point of keeping the choice uncorrelated with the focus.

### Step 3 — Resolve the card

- **If `mode == "canonical"`**: the drawn card is your card. Skip generation.
- **If `mode == "ephemeral"`**: write one new card for the returned category, following the rules in:

  `${CLAUDE_PLUGIN_ROOT}/skills/lateral-prompts/references/lateral-prompts.md`

  Read the **Categories** and **Guidelines for writing new cards** sections before writing. The card must:

  - Match the spirit of its assigned category (Strategy / Gnomic / Permission / Body / Maker psychology / Tactical / Koan)
  - Be under 9 words (most under 5)
  - Be imperative or fragment, no explanation
  - Have no hedges ("maybe," "consider," "try to")
  - Not duplicate the lateral pull of any card already in the canonical deck

You now have exactly one card.

### Step 4 — Set up the session directory

Pick a writable session root before creating any files. Different Claude surfaces sandbox writes differently — `/tmp/` is reliable on Claude Code but blocked on Claude Cowork — so probe down this ladder and stop at the first rung where directory creation succeeds:

1. `$TMPDIR/draw-1/<YYYY-MM-DD-HHMM>-<slug>/` — system temp, set on macOS and most sandboxed environments.
2. `/tmp/draw-1/<YYYY-MM-DD-HHMM>-<slug>/` — Linux fallback when `$TMPDIR` is unset.
3. `./.draw-1/<YYYY-MM-DD-HHMM>-<slug>/` — working-directory fallback when neither temp path is writable.

`<slug>` is a 2–4-word kebab-case summary of the focus (e.g., `pricing-tier-redesign`). The resolved absolute path is the session root. Use it everywhere downstream and pass it verbatim into the explorer's spawn prompt in Step 5.

Write into the resolved session root:

- `focus-brief.md` — the brief from Step 1
- `card-drawn.json` — the script output, with the ephemeral card text added if you wrote one in Step 3

### Step 5 — Spawn one lateral explorer

Spawn a single `lateral-explorer` subagent. The isolated context keeps the explorer's reading deep and uncontaminated by this conversation, and keeps the main context clean.

```
You have one card to explore against a focus area. Your context is isolated, so your reading of the card is your own.

CARD: <card text>
CATEGORY: <category if known, otherwise "unknown">

FOCUS BRIEF: read <session-dir>/focus-brief.md

DELIVERABLE: write your exploration to <session-dir>/card-<short-slug>.md

Follow the structure in your agent instructions exactly. Sharp, concrete, no hedging. Three genuinely distinct directions, not three flavors of one. Expand each direction in depth before committing to the bold proposal — the proposal is a synthesis, not a leap from stubs.
```

Substitute `<session-dir>` with the absolute path resolved in Step 4. `<short-slug>` is a 1–3-word kebab-case version of the card text. The category is known only when the draw was ephemeral (Step 3); for a canonical draw, pass "unknown".

### Step 6 — Synthesize

When the deliverable exists, read it and write `synthesis.md` in the session directory using this exact structure:

```markdown
# Draw-1 Synthesis — <focus slug>

**Focus:** <one sentence>
**Card:** <card text> (<canonical | ephemeral: category>)
**Session:** <session directory path>

## Three most creative directions

The directions from the exploration most likely to unlock something new. Pick the boldest, most unexpected, most generative. Not the safest. Not a balanced survey.

1. **<name>** — <2–4 sentences. Why this is generative.>
2. **<name>** — <2–4 sentences.>
3. **<name>** — <2–4 sentences.>

## Concrete refinements

Specific, applicable changes the user can make to whatever they're working on right now. Edit / add / cut. Each refinement names what changes and why.

- <refinement>
- <refinement>
- <refinement>

## Suggested next steps for deeper exploration

Two or three next moves the user could take if they want to push further on the most promising threads.

- <next step>
- <next step>
```

Synthesizing is judgment work, not summarization. Pick. Apply. The user wants ideas they can use, not a transcript of the exploration.

Before moving to Step 7, run this self-check on the synthesis:

- [ ] "Three most creative directions" lists exactly three, genuinely distinct (not three flavors of one)
- [ ] At least three concrete refinements the user can apply today
- [ ] At least two suggested next steps for deeper exploration
- [ ] Voice is sharp and specific, no CEO speak ("leverage", "synergize", "drive impact")

If any check fails, revise `synthesis.md` and re-run the self-check before presenting.

### Step 7 — Present to the user

Reply to the user with:

1. The session directory path (so they can read the full deliverable).
2. The full content of `synthesis.md` inline.

Keep prose around the synthesis minimal. The synthesis already says what needs saying.

## Revisions

If the user replies with feedback after Step 7, route by intent:

- **Lightweight edit** ("tighten direction 2", "drop refinement 3", "swap the language"): edit `synthesis.md` directly, re-run the Step 6 self-check, present the diff.
- **Substantive miss** ("you skipped what the card actually said", "the bold proposal wasn't carried through"): re-synthesize from the existing deliverable. Do not re-spawn the explorer and do not re-draw — the original exploration is the asset.
- **Fundamental refocus** ("the focus brief was wrong, here's the real focus"): start a new session. Do not patch over a wrong-focus run.

In all cases, re-run the Step 6 self-check before re-presenting.

## Difference from `/lateral-prompts`

`/lateral-prompts` draws four cards and fans out four isolated explorers, then converges — a full divergence session. `/draw-1` draws one card and runs one explorer. Use `draw-1` for a quick single nudge; use `lateral-prompts` when you want a wide spread to converge from. Both share the same deck, draw script, and explorer.

## Gotchas

- **`${CLAUDE_PLUGIN_ROOT}` resolves under Claude Code only.** On claude.ai or via the API the variable will be literal text. Adapt paths if you port this skill to another surface.
- **The script, deck, and explorer live under the `lateral-prompts` skill.** This skill deliberately reuses them via `${CLAUDE_PLUGIN_ROOT}/skills/lateral-prompts/...` and `Agent({subagent_type: "lateral-explorer"})`. If the plugin isn't loaded, those paths and the spawn call fail. Do not silently substitute `general-purpose` or copy the deck.
- **The session root is resolved at runtime, not hardcoded.** Step 4 walks a fallback ladder (`$TMPDIR` → `/tmp/` → `./.draw-1/`) and stops at the first writable location. The working-directory fallback is what makes the skill survive sandboxes that block `/tmp/` writes (e.g., Claude Cowork). If you fall back into the working directory, expect a `.draw-1/` folder to appear there — it's gitignored at the plugin root, but if the user runs the skill in a different repo they may want to ignore it locally.
- **`draw_cards.py` is Python 3 stdlib only.** No `pip install` needed. If `python3` is not on PATH, the bash invocation fails; see Step 2 for the failure protocol.
- **Don't re-roll the draw.** It is tempting when a card looks irrelevant. The lateral pull only works because the choice is uncorrelated with the focus. A re-rolled card is a hand-picked card with extra steps.
- **The 7 categories list lives in two places.** `skills/lateral-prompts/scripts/draw_cards.py` has them as a Python list and `skills/lateral-prompts/references/lateral-prompts.md` has them in prose. If you add or rename a category, update both.

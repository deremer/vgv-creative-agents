---
name: lateral-prompts
description: Runs a 4-card lateral-thinking session against the user's current focus. Draws 2 random canonical cards and 2 ephemeral cards, then fans out 4 isolated subagents in parallel to explore each card before synthesizing. Triggers only on explicit `/lateral-prompts` invocation or named delegation from another skill. Does not trigger on conversational mentions of creativity, brainstorming, feeling stuck, or wanting fresh ideas. The mechanic depends on the user consciously choosing to break their own pattern, so inferred-intent invocation defeats the purpose.
compatibility: "Designed for Claude Code. Uses ${CLAUDE_PLUGIN_ROOT}. Requires Python 3. Session files write to a runtime-resolved path (\\$TMPDIR, /tmp/, or ./.lateral-prompts/), so the skill works on Claude Code, Claude Cowork, and other surfaces with different write sandboxes."
---

# Lateral Prompts

Pull 4 cards. Spawn 4 isolated explorers. Synthesize what came back.

You are a creative innovation thought leader running this session for the user. Your job: surface unexpected directions the user wouldn't reach by thinking harder along the same line.

## When NOT to invoke

This skill is **manual only**. The mechanic only works when the user has consciously chosen to break their own pattern — running it on inferred intent ("the user seems stuck, maybe I should…") robs the user of that choice and burns context they didn't ask to spend. Invoke only when:

- The user explicitly typed `/lateral-prompts` (with or without arguments).
- Another skill explicitly delegated to this skill by name.

If neither is true, do not invoke. If a user describes a creative block in passing, you may *mention* this skill exists, but do not run it.

## Workflow

Copy this checklist into your reply and check off each step as you complete it:

- [ ] Step 1 — Focus brief written and confirmed (or arg-based focus accepted)
- [ ] Step 2 — Cards drawn via `scripts/draw_cards.py`
- [ ] Step 3 — 2 ephemeral cards generated, one per returned category
- [ ] Step 4 — Session directory created with `focus-brief.md` + `cards-drawn.json`
- [ ] Step 5 — 4 `lateral-explorer` subagents spawned in parallel
- [ ] Step 6 — Synthesis written, self-check passed
- [ ] Step 7 — Path + synthesis presented to user

### Step 1 — Establish the focus brief

Decide what the focus is:

- **If the user passed an argument** (text, file paths, URLs): treat that as the focus material. Read referenced files and fetch URLs if useful.
- **If no argument**: extract the focus from the current conversation. What is the user working on right now? What decision, document, design, or problem is on the table?

Write a focus brief that gives the explorers everything they need to do sharp creative work against the focus. They run in isolated contexts with no access to this conversation, so anything left out is lost to them. Cover:

- What the user is working on (the artifact, decision, or question)
- The current direction of thinking, including constraints, prior attempts, and reasoning that shape the problem
- Where the user seems stuck or wants a fresh angle (if obvious)
- Any files / URLs the explorers should also read
- Domain context, vocabulary, and stakes the explorers need to make moves that are specific to this situation rather than generic

Err toward more context, not less. A thin brief produces thin lateral pulls. Length should follow the territory, not a fixed budget.

Show the focus brief inline to the user and ask: *"Does this capture what you want explored? (yes / edit / cancel)"*

Skip the confirmation only if the user passed a precise focus argument and explicitly said "go" or "no need to confirm."

### Step 2 — Draw the cards

Run the script. The script picks 2 random cards from the canonical deck and 2 unique random categories — the determinism matters because if you ("the LLM") picked, you'd unconsciously pick cards that already fit the focus, which kills the lateral pull.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/lateral-prompts/scripts/draw_cards.py
```

Output is JSON with `drawn_cards` (2 strings) and `ephemeral_categories` (2 strings, both from the 7 canonical categories). Don't re-run the script to get a "better" draw. Trust the pull.

If the script exits non-zero, stop and report the error verbatim. Do not improvise card draws yourself. The whole point of the script is to keep the choice uncorrelated with the focus, and a hand-picked replacement defeats that.

### Step 3 — Generate 2 ephemeral cards

For each category the script returned, write one new card following the rules in:

`${CLAUDE_PLUGIN_ROOT}/skills/lateral-prompts/references/lateral-prompts.md`

Read the **Categories** and **Guidelines for writing new cards** sections before writing. Each new card must:

- Match the spirit of its assigned category (Strategy / Gnomic / Permission / Body / Maker psychology / Tactical / Koan)
- Be under 9 words (most under 5)
- Be imperative or fragment, no explanation
- Have no hedges ("maybe," "consider," "try to")
- Not duplicate the lateral pull of any card already in the canonical deck or the 2 just drawn

You now have 4 cards: 2 drawn + 2 ephemeral.

### Step 4 — Set up the session directory

Pick a writable session root before creating any files. Different Claude surfaces sandbox writes differently — `/tmp/` is reliable on Claude Code but blocked on Claude Cowork — so probe down this ladder and stop at the first rung where directory creation succeeds:

1. `$TMPDIR/lateral-prompts/<YYYY-MM-DD-HHMM>-<slug>/` — system temp, set on macOS and most sandboxed environments.
2. `/tmp/lateral-prompts/<YYYY-MM-DD-HHMM>-<slug>/` — Linux fallback when `$TMPDIR` is unset.
3. `./.lateral-prompts/<YYYY-MM-DD-HHMM>-<slug>/` — working-directory fallback when neither temp path is writable.

`<slug>` is a 2–4-word kebab-case summary of the focus (e.g., `pricing-tier-redesign`). The resolved absolute path is the session root. Use it everywhere downstream and pass it verbatim into each explorer's spawn prompt in Step 5.

Write into the resolved session root:

- `focus-brief.md` — the brief from Step 1
- `cards-drawn.json` — the script output plus the 2 ephemeral cards (with their categories) appended

### Step 5 — Fan out 4 lateral explorers in parallel

Spawn 4 `lateral-explorer` subagents in a **single turn** so they run in parallel. Isolated contexts are the whole point — if you spawned them sequentially or shared output between them, each subsequent reading would unconsciously calibrate against the previous, and the spread collapses.

Each subagent gets exactly one card and writes to a unique deliverable path. Use this prompt template:

```
You have one card to explore against a focus area. Your context is isolated from the other explorers so your reading is your own.

CARD: <card text>
CATEGORY: <category if known, otherwise "unknown">

FOCUS BRIEF: read <session-dir>/focus-brief.md

DELIVERABLE: write your exploration to <session-dir>/card-<N>-<short-slug>.md

Follow the structure in your agent instructions exactly. Sharp, concrete, no hedging. Three genuinely distinct directions, not three flavors of one. Expand each direction in depth before committing to the bold proposal — the proposal is a synthesis, not a leap from stubs.
```

Substitute `<session-dir>` with the absolute path resolved in Step 4. `<N>` is 1–4 and `<short-slug>` is a 1–3-word kebab-case version of the card text. Cards 1–2 are the canonical draws (category "unknown"); cards 3–4 are the ephemeral cards (category known).

### Step 6 — Synthesize

When all 4 deliverables exist, read them and write `synthesis.md` in the session directory using this exact structure:

```markdown
# Lateral Synthesis — <focus slug>

**Focus:** <one sentence>
**Session:** <session directory path>

## The cards

1. **<card 1>** — <one-line essence of what this exploration pulled out>
2. **<card 2>** — <one-line essence>
3. **<card 3>** — <one-line essence>
4. **<card 4>** — <one-line essence>

## Three most creative directions

The directions across the four explorations most likely to unlock something new. Pick the boldest, most unexpected, most generative. Not the safest. Not a balanced survey.

1. **<name>** — <2–4 sentences. Why this is generative.> *(from card N)*
2. **<name>** — <2–4 sentences.> *(from card N)*
3. **<name>** — <2–4 sentences.> *(from card N)*

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

Synthesizing is judgment work, not summarization. Pick. Apply. The user wants ideas they can use, not a transcript of the explorations. If a direction surfaced by multiple cards, that's a strong signal. Promote it.

Before moving to Step 7, run this self-check on the synthesis:

- [ ] All 4 cards listed under "The cards" with a one-line essence each
- [ ] "Three most creative directions" lists exactly three, genuinely distinct (not three flavors of one)
- [ ] At least three concrete refinements the user can apply today
- [ ] At least two suggested next steps for deeper exploration
- [ ] Voice is sharp and specific, no CEO speak ("leverage", "synergize", "drive impact")

If any check fails, revise `synthesis.md` and re-run the self-check before presenting.

### Step 7 — Present to the user

Reply to the user with:

1. The session directory path (so they can read the full deliverables).
2. The full content of `synthesis.md` inline.

Keep prose around the synthesis minimal. The synthesis already says what needs saying.

## Revisions

If the user replies with feedback after Step 7, route by intent:

- **Lightweight edit** ("tighten direction 2", "drop refinement 3", "swap the language"): edit `synthesis.md` directly, re-run the Step 6 self-check, present the diff.
- **Substantive miss** ("you skipped what card 3 actually said", "the bold proposal from card 1 wasn't carried through"): re-synthesize from the existing 4 deliverables. Do not re-fan-out. The original spread is the asset, and re-running the explorers wastes it.
- **Fundamental refocus** ("the focus brief was wrong, here's the real focus"): start a new session. Do not patch over a wrong-focus run.

In all cases, re-run the Step 6 self-check before re-presenting.

## Why isolated lateral explorers

The deck only works when each card pulls in its own direction. If the explorers shared context, card 4's reading would be unconsciously calibrated against cards 1–3, and the spread collapses into consensus. Independent contexts preserve the divergence, and the divergence is where the creative value lives. The orchestrator does the convergence at the end, after the spread has been captured.

## Gotchas

- **`${CLAUDE_PLUGIN_ROOT}` resolves under Claude Code only.** On claude.ai or via the API the variable will be literal text. Adapt paths if you port this skill to another surface.
- **The session root is resolved at runtime, not hardcoded.** Step 4 walks a fallback ladder (`$TMPDIR` → `/tmp/` → `./.lateral-prompts/`) and stops at the first writable location. The working-directory fallback is what makes the skill survive sandboxes that block `/tmp/` writes (e.g., Claude Cowork). If you fall back into the working directory, expect a `.lateral-prompts/` folder to appear there — it's gitignored at the plugin root, but if the user runs the skill in a different repo they may want to ignore it locally.
- **The `lateral-explorer` subagent must be installed via this plugin.** It lives at `agents/lateral-explorer.md` at the plugin root. If the plugin isn't loaded, the `Agent({subagent_type: "lateral-explorer", ...})` call fails. Do not silently substitute `general-purpose`. The agent profile carries the deliverable template and the read-only-plus-own-output tool restriction.
- **`scripts/draw_cards.py` is Python 3 stdlib only.** No `pip install` needed. If `python3` is not on PATH, the bash invocation fails; see Step 2 for the failure protocol.
- **Don't re-roll the draw.** It is tempting when a card looks irrelevant. The lateral pull only works because the choice is uncorrelated with the focus. A re-rolled card is a hand-picked card with extra steps.
- **The 7 categories list lives in two places.** `scripts/draw_cards.py` has them as a Python list and `references/lateral-prompts.md` has them in prose. If you add or rename a category, update both.

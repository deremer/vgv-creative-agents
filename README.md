# Lateral Prompts

A deck of lateral-thinking prompts for Claude Code. When you're stuck, run `/lateral-prompts` and Claude draws four cards, spawns four isolated subagents to explore your work through each card, then synthesizes what came back.

The cards exist to break stuck thinking, not to think faster along the same line. They work because the draw is uncorrelated with your problem, so the cards pull you into territory you wouldn't reach by pushing harder on the same idea.

## What it does

When you invoke the skill, Claude runs a 7-step workflow:

1. Writes a focus brief from the current conversation (or from the argument you passed) and confirms it with you.
2. Runs a Python script that draws 2 random cards from a 150-card canonical deck plus 2 random categories.
3. Generates 2 fresh ephemeral cards on the fly, one per drawn category, so no two sessions are identical.
4. Creates a session directory under `/tmp/lateral-prompts/` with the brief and the cards.
5. Fans out 4 `lateral-explorer` subagents in parallel. Each gets exactly one card. None see the others' output.
6. Synthesizes the four explorations into three creative directions, concrete refinements you can apply today, and suggested next moves for deeper exploration.
7. Hands you the synthesis inline plus the path to the full session artifacts.

Isolated contexts are load-bearing. If the explorers shared state, card 4 would unconsciously calibrate against cards 1 to 3, and the spread would collapse into consensus. The divergence is where the creative value lives. The orchestrator does the convergence at the end, after the spread has been captured.

## Installation

This is a Claude Code plugin. Clone it into your plugins directory:

```bash
cd ~/.claude/plugins
git clone git@github.com:deremer/lateral-prompts.git
```

Once Claude Code picks up the plugin, the skill is invokable as `/lateral-prompts` and the `lateral-explorer` subagent becomes available to the orchestrator.

Requirements:

- Claude Code. The skill uses `${CLAUDE_PLUGIN_ROOT}` and spawns subagents via the Agent tool, so claude.ai and the raw API won't work without porting.
- Python 3 on PATH. Stdlib only, no pip install.
- Unix-like filesystem. Sessions write to `/tmp/lateral-prompts/`.

## How to use it

```
/lateral-prompts
```

With no argument, Claude extracts the focus from the current conversation. Useful when you've been working on something with Claude already and want a fresh angle on it.

```
/lateral-prompts the pricing page is not converting and the headline has been rewritten four times
```

With an argument, that text becomes the focus. Pass file paths or URLs and Claude will read them into the brief.

After the run, you get a session directory containing the focus brief, the four card explorations, and `synthesis.md`. The synthesis is the headline output. The individual explorations are there if you want to see what didn't make the cut.

If the synthesis misses something, you can ask for a revision. Light edits get applied directly. A substantive miss triggers a re-synthesis from the existing four explorations. A wrong focus brief means starting a new session, since patching over a wrong-focus run wastes the spread.

## When to use it

- You've rewritten the same paragraph six times and each version is slightly worse.
- A strategy doc that reads correct and feels lifeless.
- Choosing between two options that both feel right, where the conversation keeps going in circles.
- A pitch, deck, or memo where the structure is fine but the thing has no edge.
- Product or design decisions where every direction sounds reasonable, which is itself the signal that you're stuck on the same plane.
- Naming. Especially naming. Naming is where lateral pulls earn their keep.
- Any moment you catch yourself thinking "I just need to think about this harder."

## When not to use it

The mechanic only works when you have consciously chosen to break your own pattern. Claude will not run this skill on inferred intent. If you mention being stuck in passing, Claude may point at the skill, but the choice to invoke is yours. That choice is part of why it works.

Also skip it for:

- Tasks with a clear right answer. The deck doesn't help when there's nothing to break.
- Implementation work. Cards pull on direction, not execution.
- Research questions where you just need a fact. Use docs or web search.

## How the cards are made

The deck mixes seven categories. You don't need to know which is which when you draw. Knowing helps when you're writing new ones.

- **Strategy.** Imperative moves on the work itself. *Subtract until it hurts. Reverse the flow.*
- **Gnomic.** A single word or fragment. *Saturation. Hinge. Husk.* Interpretation is the work.
- **Permission.** Lets the maker off a hook they put themselves on. *It's allowed to be small. Nothing today is fine.*
- **Body.** Engages the maker as a physical creature. *Stand up. Where is the tension in your jaw.*
- **Maker psychology.** Interrogates the person, not the artifact. *Whose voice are you using. The fear is information.*
- **Tactical.** A specific studio move. *Use only the rejected pieces. Restart with the third draft.*
- **Koan.** Resists easy interpretation. *A door is also a wall. The slow path arrives first.*

Rules for cards:

- Imperative or fragment, never explanation.
- Under nine words. Most under five.
- No hedges. Cut "maybe," "consider," "try to."
- No CEO voice. No "leverage," "drive impact," "align stakeholders."
- One move per card.
- If a card sounds like a LinkedIn post, it's wrong. If it sounds like a friend who knows the work, it's right.

The full canonical deck of 150 cards lives in `skills/lateral-prompts/references/lateral-prompts.md`. Edit that file directly to add or remove cards. The draw script reads from it at runtime.

## Repo layout

```
.claude-plugin/plugin.json              plugin manifest
agents/lateral-explorer.md              subagent profile spawned per card
skills/lateral-prompts/SKILL.md         orchestrator skill
skills/lateral-prompts/scripts/         draw_cards.py
skills/lateral-prompts/references/      canonical deck and writing rules
skills/lateral-prompts/evals/           evals for the skill
```

## Credits

The workflow and deck are by Very Good Ventures. Inspired by Brian Eno and Peter Schmidt's *Oblique Strategies* (1975), frog design's frogthink random-entry technique, and other lateral-thinking practices that use chance to break stuck patterns.

## License

MIT. See [LICENSE](LICENSE).

# session-tokens

A Claude Code skill that reports how many tokens a working session consumed —
the main conversation **and every subagent it spawned** — broken down by model,
effort level, agent and skill, with an estimated cost at API list prices and a
short list of insights.

It reads the transcripts Claude Code already writes to `~/.claude/projects/`.
There are no API calls, no dependencies beyond the Python standard library, and
nothing leaves your machine.

---

## Install

Copy (or symlink) the folder into your user-level skills directory:

```bash
# copy
cp -R session-tokens ~/.claude/skills/

# or symlink, so a `git pull` here updates the installed skill
ln -s "$(pwd)/session-tokens" ~/.claude/skills/session-tokens
```

Skills are picked up when a session starts, so open a new Claude Code session
afterwards. Requires `python3` (3.9+) on your `PATH`.

## Use

In any Claude Code session:

| Command | Reports on |
|---|---|
| `/session-tokens` | The current session |
| `/session-tokens last` | The most recent *other* session in this project that made API calls |
| `/session-tokens <session-id>` | A specific session; a unique prefix of the id is enough |
| `/session-tokens --project` | Every session in the current project, plus a per-session table |
| `/session-tokens --project --since 2026-09-01` | Project sessions active on or after that date |
| `/session-tokens --project --top 10` | Same, listing the 10 costliest agents and rolling the rest into one row (default 25 with `--project`; `0` lists all) |

You can also just ask — *"how many tokens did this session use?"*, *"what did
the subagents cost?"*, *"which models and effort levels ran today?"* — and
Claude will pick the skill up from its description.

### Running the script directly

The skill is a thin wrapper around one script, which works on its own:

```bash
python3 ~/.claude/skills/session-tokens/scripts/session_tokens.py            # current session*
python3 ~/.claude/skills/session-tokens/scripts/session_tokens.py last
python3 ~/.claude/skills/session-tokens/scripts/session_tokens.py 1a4df5a2
python3 ~/.claude/skills/session-tokens/scripts/session_tokens.py --project --since 2026-09-01
python3 ~/.claude/skills/session-tokens/scripts/session_tokens.py --json     # raw numbers
```

\* "Current session" comes from `$CLAUDE_CODE_SESSION_ID`, which is only set
inside Claude Code. From a plain terminal, pass a session id, `last` or
`--project`. `last` and `--project` find the project from the current working
directory, so run them from the project's root.

## What you get

Seven tables, then Claude's insights and caveats. An abridged example from a real
session:

```text
## Token report — session `ebfb6145-…`

2026-09-17T15:46:54Z → 2026-09-18T04:19:28Z (12h 32m span) · 1396 API calls · 17 subagent(s)

| Scope | Calls | Input | Cache write | Cache read | Output | …of which thinking | Est. cost |
|---|---|---|---|---|---|---|---|
| All   | 1396  | 7.0k  | 3.92M       | 261.28M    | 453k   | 94k                | $103.24   |

- Estimated cost: $103.24 at API list prices (as of 2026-06-24)
- Cache hit rate: 99% of input tokens served from cache
- Thinking: 21% of output tokens
- Subagents: 44% of estimated cost
- Cost by token type: cache reads 72%, cache writes 19%, output 9%, fresh input 0%

### By model   — opus-5 174 calls $57.71 · sonnet-5 1222 calls $45.53
### By effort  — one row per effort level (Haiku shows n/a: it has no effort setting)
### By agent   — main session(s), then each subagent with its type, task description and model
### By skill   — which skill or slash command was active when each call was made
```

| Column | Meaning |
|---|---|
| **Input** | Fresh, uncached input tokens |
| **Cache write** | Context written to the prompt cache (5-minute and 1-hour TTL combined; priced separately) |
| **Cache read** | Context re-read from cache on each turn. Nearly all the tokens, and cheap per token, but in long sessions often the largest share of cost — see the "Cost by token type" line |
| **Output** | Generated tokens, thinking included |
| **…of which thinking** | The part of Output spent on reasoning |
| **Est. cost** | API-list-price estimate for that row |

## How the numbers are produced

| Data | Where it comes from |
|---|---|
| Main conversation | `~/.claude/projects/<project>/<session>.jsonl` |
| Subagents | `<session>/subagents/agent-*.jsonl`, labelled from the sibling `.meta.json` (`agentType`, `description`) |
| Tokens | `message.usage` on each assistant record |
| Model | `message.model` |
| Effort | `perTurnEffort`, falling back to `effort` |
| Skill | `attributionSkill` |

**De-duplication matters.** Claude Code writes one transcript line per content
block, and each line repeats the full `usage` of the response. Summing lines
naively over-counts — in one tested session, 67 lines covered 28 real API calls.
The script counts each `message.id` once, and its totals were cross-checked
against an independent `jq` count of the same transcript.

## Caveats

- **Cost is an estimate** at Anthropic's first-party API list prices. On a
  Claude Pro/Max/Team subscription it is an *API-equivalent* figure, not what
  you are billed.
- **The reply being written is not counted.** Responses reach the transcript
  only once complete, so a report on the live session excludes the turn that
  produced it.
- **The transcript format is internal to Claude Code**, not a public API. If a
  report suddenly shows zero calls for a session that clearly did work, check a
  transcript line against the table above — a field may have moved.

## Updating prices

Prices live in the `PRICES` table at the top of
`scripts/session_tokens.py`, with a `PRICES_AS_OF` date that is printed in every
report. Each entry is `model-id prefix: (input, output, cache_read,
fast_multiplier)` in $ per million tokens; cache writes are derived as 1.25×
(5-minute) and 2× (1-hour) the input price. Models missing from the table are
reported, but their calls are left out of the cost and flagged as unpriced.

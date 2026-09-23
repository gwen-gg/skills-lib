---
name: session-tokens
description: Report how many tokens a Claude Code working session consumed — main conversation and every subagent — broken down by model, effort level, agent and skill, with an estimated API-list-price cost and a few insights. Use when the user asks how many tokens/how much a session cost, what models or effort levels were used, how much the subagents consumed, or wants a usage report for this session, the previous one, or the whole project.
argument-hint: "[last | <session-id> | --project [--since YYYY-MM-DD]]"
---

# Session token report

The numbers come from `scripts/session_tokens.py`, never from reading transcripts
by hand: every API response is logged once per content block with its `usage`
repeated, so a naive sum over-counts (a sample session had 67 assistant lines for
28 real calls). The script de-duplicates on `message.id`.

## 1. Run the script

```bash
python3 ~/.claude/skills/session-tokens/scripts/session_tokens.py [ARGS]
```

Pass the user's argument through unchanged:

| Argument | Scope |
|---|---|
| *(none)* | This session, from `$CLAUDE_CODE_SESSION_ID` |
| `last` | The most recent *other* session in this project that made API calls |
| `<session-id>` or a unique prefix | That session, in any project |
| `--project [--since YYYY-MM-DD]` | Every session in this project, plus a per-session table |
| `--json` | Same data as JSON, if you need to compute something the tables don't show |

It needs only the Python standard library and reads only local files under
`~/.claude/projects/`. Run it from the project's working directory; `last` and
`--project` locate the project folder from the cwd.

## 2. Present the report

Relay the script's markdown tables as-is: the numbers are exact, so don't round,
re-add or restate them in prose. Drop a table only when it has a single row that
repeats the Totals row (e.g. "By effort" when everything ran at one effort), and
say so in one line.

Then add **Insights**: at most five bullets, each tied to a number in the tables.
Pick the ones that are actually true of this report:

- **Where the money went.** The top one or two agents or skills by cost, and
  their share of the total.
- **Main thread vs subagents.** Subagents' share of cost. If a cheaper model
  (Sonnet, Haiku) did most of the calls but the main thread's model dominates
  cost, say so: that is the orchestrator's context being re-read every turn.
- **Cache behaviour.** A cache hit rate above ~90% is normal for Claude Code.
  Cache reads usually make up most of the tokens but not most of the cost, so
  don't present the raw token total as "consumption" without that context. A low
  hit rate or large cache writes point to context being rebuilt (compaction,
  model switch, long idle gaps beyond the cache TTL).
- **Thinking.** Its share of output, and whether it tracks the effort level.
- **Effort.** Which levels ran where. Haiku does not support effort, so its calls
  show `n/a`; that is expected, not missing data.
- **Anything odd.** Unpriced models, fast-mode calls, one subagent far costlier
  than its siblings (and its description, so the user can tell which task it was).

## 3. Always state these caveats, briefly

- **The cost is an estimate** at Anthropic API list prices, as of the date the
  report prints. On a Claude subscription it is an API-equivalent figure, not
  what the user is billed. Prices live in `PRICES` at the top of the script;
  if the report's model list includes a model missing from it, say its calls
  were left out of the cost.
- **The current reply is not counted.** A response is written to the transcript
  only once it is complete, so a report on the live session misses the turn
  that produced it.

## Where the data comes from

| Field | Source |
|---|---|
| Tokens | `message.usage` on each assistant record: `input_tokens`, `cache_creation.ephemeral_{5m,1h}_input_tokens`, `cache_read_input_tokens`, `output_tokens`, `output_tokens_details.thinking_tokens` |
| Model | `message.model` (`<synthetic>` placeholder records are skipped) |
| Effort | `perTurnEffort`, falling back to `effort` |
| Skill | `attributionSkill`, the skill that was active when the call was made |
| Fast mode | `usage.speed == "fast"`, priced at the model's fast-mode multiplier |
| Subagents | `<session>/subagents/agent-*.jsonl`, labelled from the sibling `.meta.json` (`agentType`, `description`) |

These are Claude Code's internal transcript formats, not a public API. If a
report comes back with zero calls for a session that clearly did work, check a
transcript line against this table before trusting the numbers: a field may have
moved.

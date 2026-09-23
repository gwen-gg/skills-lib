#!/usr/bin/env python3
"""Report token usage for a Claude Code session, subagents included.

Reads the transcripts Claude Code writes under ~/.claude/projects/:

    <project>/<session>.jsonl                      main conversation
    <project>/<session>/subagents/agent-*.jsonl    one file per subagent
    <project>/<session>/subagents/agent-*.meta.json  agentType, description, model

Every API response is logged once per content block, each line repeating the
full `usage`, so records are de-duplicated on message.id before summing.

Usage:
    session_tokens.py                  current session ($CLAUDE_CODE_SESSION_ID)
    session_tokens.py last             most recent *other* session in this project
    session_tokens.py <session-id>     a specific session (prefix accepted)
    session_tokens.py --project [--since YYYY-MM-DD]   every session in this project
    add --json for machine-readable output
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"

# $/MTok, Anthropic first-party API list prices. Cache writes are 1.25x input
# (5-minute TTL) and 2x input (1-hour TTL); cache reads are priced per model.
# Source: claude-api skill model table, cached 2026-06-24. Update when prices move.
PRICES_AS_OF = "2026-06-24"
PRICES = {
    # prefix: (input, output, cache_read, fast_multiplier or None)
    "claude-fable-5-1": (10.0, 50.0, 0.25, None),
    "claude-mythos-5-1": (10.0, 50.0, 0.25, None),
    "claude-fable-5": (10.0, 50.0, 1.00, None),
    "claude-opus-5-5": (4.0, 20.0, 0.20, 2.0),
    "claude-opus-5": (5.0, 25.0, 0.50, 2.0),
    "claude-opus-4-8": (5.0, 25.0, 0.50, None),
    "claude-opus-4-7": (5.0, 25.0, 0.50, None),
    "claude-opus-4-6": (5.0, 25.0, 0.50, None),
    "claude-sonnet-5": (2.0, 10.0, 0.20, None),
    "claude-sonnet-4-6": (3.0, 15.0, 0.30, None),
    "claude-haiku-4-5": (1.0, 5.0, 0.10, None),
}

FIELDS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output", "thinking")


def price_for(model):
    # Longest prefix wins, so claude-opus-5-5 is not priced as claude-opus-5.
    for prefix in sorted(PRICES, key=len, reverse=True):
        if model.startswith(prefix):
            return PRICES[prefix]
    return None


def cost_of(model, speed, t):
    p = price_for(model)
    if p is None:
        return None
    inp, out, read, fast = p
    mult = fast if (speed == "fast" and fast) else 1.0
    return mult * (
        t["input"] * inp
        + t["cache_write_5m"] * inp * 1.25
        + t["cache_write_1h"] * inp * 2.0
        + t["cache_read"] * read
        + t["output"] * out
    ) / 1_000_000


def project_dir():
    # Claude Code names the folder after the cwd with '/' and '.' turned into '-'.
    name = "".join("-" if c in "/." else c for c in os.getcwd())
    d = PROJECTS / name
    return d if d.is_dir() else None


def find_session(ref):
    """Return the main transcript path for a session id or unique id prefix."""
    hits = [p for p in PROJECTS.glob(f"*/{ref}*.jsonl")]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"no transcript found for session '{ref}'")
    sys.exit(f"session prefix '{ref}' is ambiguous: " + ", ".join(p.stem for p in hits))


def read_records(path):
    """Yield assistant records with usage, de-duplicated on message id."""
    seen = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if '"assistant"' not in line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # a line being written right now
            if r.get("type") != "assistant":
                continue
            msg = r.get("message") or {}
            usage = msg.get("usage")
            model = msg.get("model") or ""
            if not usage or model == "<synthetic>":
                continue
            key = msg.get("id") or r.get("requestId") or r.get("uuid")
            if key in seen:
                continue
            seen.add(key)
            cc = usage.get("cache_creation") or {}
            w5 = cc.get("ephemeral_5m_input_tokens")
            w1 = cc.get("ephemeral_1h_input_tokens")
            if w5 is None and w1 is None:
                w5, w1 = usage.get("cache_creation_input_tokens", 0), 0
            yield {
                "model": model,
                "speed": usage.get("speed") or "standard",
                "effort": r.get("perTurnEffort") or r.get("effort") or "n/a",
                "skill": r.get("attributionSkill") or "(none)",
                "ts": r.get("timestamp"),
                "tokens": {
                    "input": usage.get("input_tokens", 0) or 0,
                    "cache_write_5m": w5 or 0,
                    "cache_write_1h": w1 or 0,
                    "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
                    "output": usage.get("output_tokens", 0) or 0,
                    "thinking": (usage.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0,
                },
            }


def session_sources(main_path):
    """(label, kind, meta, path) for the main transcript and each subagent."""
    yield ("main", "main", {}, main_path)
    sub = main_path.with_suffix("") / "subagents"
    if not sub.is_dir():
        return
    for p in sorted(sub.rglob("agent-*.jsonl")):
        meta_path = p.with_suffix(".meta.json")
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        yield (p.stem.removeprefix("agent-"), "subagent", meta, p)


def empty():
    return {f: 0 for f in FIELDS} | {"calls": 0, "cost": 0.0, "unpriced_calls": 0}


def add(bucket, rec):
    for f in FIELDS:
        bucket[f] += rec["tokens"][f]
    bucket["calls"] += 1
    c = cost_of(rec["model"], rec["speed"], rec["tokens"])
    if c is None:
        bucket["unpriced_calls"] += 1
    else:
        bucket["cost"] += c


def analyse(main_paths):
    total = empty()
    by_model, by_effort, by_skill = (defaultdict(empty) for _ in range(3))
    by_source = {}
    by_session = {}
    first = last = None
    fast_calls = 0

    for main_path in main_paths:
        sess = empty()
        for label, kind, meta, path in session_sources(main_path):
            src_key = f"{main_path.stem[:8]}:{label}" if len(main_paths) > 1 else label
            src = by_source.setdefault(src_key, empty() | {
                "kind": kind,
                "agent_type": meta.get("agentType") or ("main session" if kind == "main" else "?"),
                "description": meta.get("description") or "",
                "models": set(),
            })
            for rec in read_records(path):
                for b in (total, sess, src, by_model[rec["model"]],
                          by_effort[rec["effort"]], by_skill[rec["skill"]]):
                    add(b, rec)
                src["models"].add(rec["model"])
                if rec["speed"] == "fast":
                    fast_calls += 1
                if rec["ts"]:
                    first = min(first or rec["ts"], rec["ts"])
                    last = max(last or rec["ts"], rec["ts"])
        if sess["calls"]:
            by_session[main_path.stem] = sess

    for s in by_source.values():
        s["models"] = sorted(s["models"])
    by_source = {k: v for k, v in by_source.items() if v["calls"]}

    return {
        "sessions": list(by_session) or [p.stem for p in main_paths],
        "first": first,
        "last": last,
        "prices_as_of": PRICES_AS_OF,
        "fast_calls": fast_calls,
        "total": total,
        "by_model": dict(by_model),
        "by_effort": dict(by_effort),
        "by_skill": dict(by_skill),
        "by_source": by_source,
        "by_session": by_session if len(by_session) > 1 else {},
    }


# ---------- rendering ----------

def n(x):
    if x >= 1_000_000:
        return f"{x / 1_000_000:.2f}M"
    if x >= 10_000:
        return f"{x / 1000:.0f}k"
    if x >= 1000:
        return f"{x / 1000:.1f}k"
    return str(x)


def usd(x):
    return f"${x:,.2f}" if x >= 0.01 or x == 0 else "<$0.01"


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "—"


def row_cells(b):
    writes = b["cache_write_5m"] + b["cache_write_1h"]
    return [str(b["calls"]), n(b["input"]), n(writes), n(b["cache_read"]),
            n(b["output"]), n(b["thinking"]), usd(b["cost"])]


HEAD = ["Calls", "Input", "Cache write", "Cache read", "Output", "…of which thinking", "Est. cost"]


def table(title, first_col, rows):
    out = [f"### {title}", "", "| " + " | ".join([first_col] + HEAD) + " |",
           "|" + "---|" * (len(HEAD) + 1)]
    out += ["| " + " | ".join([label] + row_cells(b)) + " |" for label, b in rows]
    return "\n".join(out) + "\n"


def duration(first, last):
    try:
        a = datetime.fromisoformat(first.replace("Z", "+00:00"))
        b = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return "?"
    mins = int((b - a).total_seconds() // 60)
    return f"{mins // 60}h {mins % 60:02d}m" if mins >= 60 else f"{mins}m"


def render(r):
    t = r["total"]
    by_cost = lambda d: sorted(d.items(), key=lambda kv: (-kv[1]["cost"], -kv[1]["calls"]))
    all_in = t["input"] + t["cache_write_5m"] + t["cache_write_1h"] + t["cache_read"]
    sub_cost = sum(s["cost"] for s in r["by_source"].values() if s["kind"] == "subagent")
    sub_n = sum(1 for s in r["by_source"].values() if s["kind"] == "subagent")

    sess = r["sessions"]
    scope = f"session `{sess[0]}`" if len(sess) == 1 else f"{len(sess)} sessions"
    out = [f"## Token report — {scope}", "",
           f"{r['first'] or '?'} → {r['last'] or '?'} ({duration(r['first'], r['last'])} span) · "
           f"{t['calls']} API calls · {sub_n} subagent(s)", ""]

    out.append(table("Totals", "Scope", [("All", t)]))

    headline = [
        f"- **Estimated cost:** {usd(t['cost'])} at API list prices (as of {r['prices_as_of']})"
        + (f"; {t['unpriced_calls']} call(s) on unpriced models excluded" if t["unpriced_calls"] else ""),
        f"- **Cache hit rate:** {pct(t['cache_read'], all_in)} of input tokens served from cache",
        f"- **Thinking:** {pct(t['thinking'], t['output'])} of output tokens",
        f"- **Subagents:** {pct(sub_cost, t['cost'])} of estimated cost",
    ]
    if r["fast_calls"]:
        headline.append(f"- **Fast mode:** {r['fast_calls']} call(s), priced at the fast-mode premium")
    out += headline + [""]

    out.append(table("By model", "Model", by_cost(r["by_model"])))
    out.append(table("By effort", "Effort", by_cost(r["by_effort"])))

    src_rows = []
    for key, s in by_cost(r["by_source"]):
        label = s["agent_type"] if s["kind"] == "main" else f"{s['agent_type']} ({key})"
        if s["description"]:
            label += f" — {s['description']}"
        label += f" · {', '.join(m.removeprefix('claude-') for m in s['models'])}"
        src_rows.append((label.replace("|", "/"), s))
    out.append(table("By agent", "Agent", src_rows))

    out.append(table("By skill", "Skill", by_cost(r["by_skill"])))

    if r["by_session"]:
        out.append(table("By session", "Session", by_cost(r["by_session"])))

    out.append("_Input = uncached input. Cache reads are re-sent context billed at a "
               "fraction of the input rate. Thinking is included in Output. The reply "
               "currently being written is not in the transcript yet, so it is not counted._")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", nargs="?", help="session id or prefix, or 'last'")
    ap.add_argument("--project", action="store_true", help="aggregate every session in this project")
    ap.add_argument("--since", help="with --project: only sessions active on/after YYYY-MM-DD")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    a = ap.parse_args()

    current = os.environ.get("CLAUDE_CODE_SESSION_ID")

    if a.project:
        d = project_dir()
        if not d:
            sys.exit(f"no Claude Code project folder for {os.getcwd()}")
        paths = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if a.since:
            cutoff = datetime.fromisoformat(a.since).timestamp()
            paths = [p for p in paths if p.stat().st_mtime >= cutoff]
    elif a.session == "last":
        d = project_dir()
        if not d:
            sys.exit(f"no Claude Code project folder for {os.getcwd()}")
        others = sorted((p for p in d.glob("*.jsonl") if p.stem != current),
                        key=lambda p: p.stat().st_mtime, reverse=True)
        # Skip sessions with no API calls (e.g. one opened only to run /model).
        paths = [next((p for p in others if next(read_records(p), None)), None)]
        if paths[0] is None:
            sys.exit("no previous session with API calls in this project")
    elif a.session:
        paths = [find_session(a.session)]
    elif current:
        paths = [find_session(current)]
    else:
        sys.exit("not inside a Claude Code session; pass a session id, 'last' or --project")

    if not paths:
        sys.exit("no sessions matched")

    r = analyse(paths)
    print(json.dumps(r, indent=2, default=str) if a.json else render(r))


if __name__ == "__main__":
    main()

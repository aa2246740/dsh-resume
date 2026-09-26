#!/usr/bin/env bash
# Deny subagentStart for claude, sonnet, opus, computerUse, and browser.
set -eu
payload=$(cat || true)
python3 -c '
import json, sys
raw = sys.stdin.read().lstrip("\ufeff")
try:
    data = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    json.dump({
        "permission": "deny",
        "user_message": "Blocked subagent start: hook payload was not valid JSON.",
    }, sys.stdout)
    raise SystemExit(0)
if not isinstance(data, dict):
    data = {}
fields = [
    data.get("subagent_type"),
    data.get("subagent_model"),
    data.get("model"),
    data.get("model_id"),
]
compact = "".join(ch.lower() if ch.isalnum() else " " for ch in " ".join(str(item) for item in fields if item))
compact = "".join(compact.split())
denied = ("claude", "sonnet", "opus", "computeruse", "browser")
if any(needle in compact for needle in denied):
    json.dump({
        "permission": "deny",
        "user_message": "Blocked subagent start: claude, sonnet, opus, computerUse, and browser subagents are denied. Inherit the parent model.",
    }, sys.stdout)
else:
    json.dump({"permission": "allow"}, sys.stdout)
' <<<"$payload"

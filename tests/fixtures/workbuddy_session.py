#!/usr/bin/env python3
"""Build a WorkBuddy projects/<slug>/<sessionId>.jsonl fixture tree."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


WIDGET_ID = "workbuddy-session-widget"
GADGET_ID = "workbuddy-session-gadget"
QUICKASK_ID = "workbuddy-session-quickask"
OTHER_ID = "workbuddy-session-other"


def _slug(cwd: str) -> str:
    base = re.sub(r"[/\\:]", "-", cwd)
    base = re.sub(r"-+", "-", base.strip("-"))
    return base


def _record(**kwargs: object) -> dict[str, object]:
    return kwargs


def _message(
    session_id: str,
    cwd: str,
    record_id: str,
    role: str,
    content: object,
    timestamp: int,
    **extra: object,
) -> dict[str, object]:
    record = _record(
        id=record_id,
        timestamp=timestamp,
        type="message",
        role=role,
        content=content,
        sessionId=session_id,
        cwd=cwd,
    )
    record.update(extra)
    return record


def _write(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build(home: Path, cwd: Path, other_cwd: Path) -> Path:
    projects = home / "projects"
    cwd_text = str(cwd)
    other_text = str(other_cwd)

    widget = [
        _message(
            WIDGET_ID, cwd_text, "widget-user", "user",
            [{
                "type": "input_text",
                "text": (
                    "<system-reminder>hidden context</system-reminder>"
                    "<user_query>Continue the WorkBuddy fixture.</user_query>"
                ),
            }],
            1_755_648_000_000,
        ),
        _record(
            id="widget-reasoning",
            timestamp=1_755_648_010_000,
            type="reasoning",
            sessionId=WIDGET_ID,
            cwd=cwd_text,
            rawContent=[{"type": "reasoning_text", "text": "WORKBUDDY_PRIVATE_REASONING"}],
        ),
        _message(
            WIDGET_ID, cwd_text, "widget-assistant", "assistant",
            [{"type": "output_text", "text": "Prepared the WorkBuddy change."}],
            1_755_648_020_000,
            model="wb-auto",
        ),
        _record(
            id="widget-call",
            timestamp=1_755_648_030_000,
            type="function_call",
            callId="wb-call-1",
            name="shell",
            arguments=json.dumps({"command": "pnpm test"}),
            status="completed",
            sessionId=WIDGET_ID,
            cwd=cwd_text,
        ),
        _record(
            id="widget-result",
            timestamp=1_755_648_040_000,
            type="function_call_result",
            callId="wb-call-1",
            output="workbuddy focused tests passed",
            status="completed",
            sessionId=WIDGET_ID,
            cwd=cwd_text,
        ),
        _message(
            WIDGET_ID, cwd_text, "widget-meta", "user",
            [{"type": "input_text", "text": "WORKBUDDY_META_RECORD"}],
            1_755_648_050_000,
            providerData={"isMeta": True},
        ),
        _message(
            WIDGET_ID, cwd_text, "widget-steer", "user",
            [{"type": "input_text", "text": "WORKBUDDY_STEER_RECORD"}],
            1_755_648_055_000,
            providerData={"clientMeta": {"codebuddy.ai": {"queueOrigin": "steer"}}},
        ),
        _record(
            id="widget-summary",
            timestamp=1_755_648_060_000,
            type="summary",
            summary="Compacted the WorkBuddy fixture.",
            sessionId=WIDGET_ID,
            cwd=cwd_text,
        ),
        _record(
            id="widget-title",
            timestamp=1_755_648_070_000,
            type="ai-title",
            aiTitle="WorkBuddy widget session",
            sessionId=WIDGET_ID,
            cwd=cwd_text,
        ),
        _record(
            timestamp=1_755_648_080_000,
            type="file-history-snapshot",
            messageId="widget-assistant",
            snapshot={"messageId": "widget-assistant", "trackedFileBackups": {}},
            cwd=cwd_text,
        ),
    ]
    _write(projects / _slug(cwd_text) / f"{WIDGET_ID}.jsonl", widget)

    gadget = [
        _message(
            GADGET_ID, cwd_text, "gadget-user", "user",
            [{"type": "input_text", "text": "Continue the WorkBuddy gadget."}],
            1_755_648_400_000,
        ),
        _message(
            GADGET_ID, cwd_text, "gadget-assistant", "assistant",
            [{"type": "output_text", "text": "Gadget reply."}],
            1_755_648_500_000,
            model="wb-auto",
        ),
    ]
    _write(projects / _slug(cwd_text) / f"{GADGET_ID}.jsonl", gadget)

    quickask = [
        _message(
            QUICKASK_ID, cwd_text, "quickask-user", "user",
            [{"type": "input_text", "text": "WORKBUDDY_QUICKASK"}],
            1_755_648_600_000,
        ),
    ]
    quickask_path = projects / _slug(cwd_text) / f"{QUICKASK_ID}.jsonl"
    _write(quickask_path, quickask)
    (projects / _slug(cwd_text) / f"{QUICKASK_ID}.quickask").touch()

    other = [
        _message(
            OTHER_ID, other_text, "other-user", "user",
            [{"type": "input_text", "text": "WORKBUDDY_OTHER_WORKSPACE"}],
            1_755_649_000_000,
        ),
    ]
    _write(projects / _slug(other_text) / f"{OTHER_ID}.jsonl", other)
    return projects


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--other-cwd", type=Path)
    args = parser.parse_args()
    cwd = args.cwd.expanduser().resolve()
    other = (args.other_cwd.expanduser().resolve() if args.other_cwd else cwd / "other-workspace")
    cwd.mkdir(parents=True, exist_ok=True)
    other.mkdir(parents=True, exist_ok=True)
    print(build(args.home.expanduser().resolve(), cwd, other))


if __name__ == "__main__":
    main()

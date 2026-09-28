#!/usr/bin/env python3
"""Build Qoder transcript fixtures: projects/<slug>/<session>.jsonl plus an IDE cache file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


WIDGET_ID = "qoder-session-widget"
GADGET_ID = "qoder-session-gadget"
OTHER_ID = "qoder-session-other"
IDE_ID = "task-00aa11bb22cc33dd.session.execution"


def _slug(cwd: Path) -> str:
    return "".join(char if char.isalnum() else "-" for char in str(cwd))


def _record(
    session_id: str,
    uuid: str,
    parent: str | None,
    timestamp: str,
    cwd: str,
    record_type: str,
    message: dict[str, object] | None,
    **extra: object,
) -> dict[str, object]:
    record: dict[str, object] = {
        "type": record_type,
        "uuid": uuid,
        "parentUuid": parent,
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
        "version": "1.1.64",
        "gitBranch": "fixture-branch",
        "isSidechain": False,
        "message": message,
    }
    record.update(extra)
    return record


def _user(session_id: str, uuid: str, parent: str | None, timestamp: str, cwd: str, text: str):
    return _record(
        session_id, uuid, parent, timestamp, cwd, "user",
        {"role": "user", "content": text},
    )


def _tool_results(
    session_id: str, uuid: str, parent: str, timestamp: str, cwd: str,
    tool_use_id: str, content: str,
):
    return _record(
        session_id, uuid, parent, timestamp, cwd, "user",
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                    "is_error": False,
                }
            ],
        },
        toolUseResult={"stdout": content},
    )


def _assistant(
    session_id: str, uuid: str, parent: str, timestamp: str, cwd: str,
    content: list[dict[str, object]], **extra: object,
):
    return _record(
        session_id, uuid, parent, timestamp, cwd, "assistant",
        {"id": f"chatcmpl-{uuid}", "role": "assistant", "model": "", "content": content},
        **extra,
    )


def _write_transcript(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def build(home: Path, cwd: Path, other_cwd: Path, ide_root: Path | None) -> Path:
    root = home / "projects" / _slug(cwd)
    widget = [
        _record(
            WIDGET_ID, "widget-config", None, "2026-08-20T04:00:00.000Z", str(cwd),
            "runtime-config", None,
        ),
        _user(WIDGET_ID, "widget-user", None, "2026-08-20T04:00:01.000Z", str(cwd), "Continue the Qoder fixture."),
        _assistant(
            WIDGET_ID, "widget-assistant-1", "widget-user", "2026-08-20T04:00:02.000Z", str(cwd),
            [
                {"type": "thinking", "thinking": "QODER_PRIVATE_THINKING"},
                {"type": "text", "text": "Prepared the Qoder change."},
                {"type": "tool_use", "id": "qoder-call-1", "name": "Bash", "input": {"command": "pnpm test"}},
            ],
        ),
        _tool_results(
            WIDGET_ID, "widget-result", "widget-assistant-1", "2026-08-20T04:00:03.000Z", str(cwd),
            "qoder-call-1", "qoder focused tests passed",
        ),
        _assistant(
            WIDGET_ID, "widget-sidechain", "widget-result", "2026-08-20T04:00:04.000Z", str(cwd),
            [{"type": "text", "text": "QODER_SIDECHAIN"}],
            isSidechain=True,
        ),
        _assistant(
            WIDGET_ID, "widget-assistant-2", "widget-result", "2026-08-20T04:00:05.000Z", str(cwd),
            [{"type": "text", "text": "Stopped after the Qoder focused test."}],
        ),
        _record(
            WIDGET_ID, "widget-snapshot", "widget-assistant-2", "2026-08-20T04:00:06.000Z", str(cwd),
            "file-history-snapshot", None,
        ),
        _record(
            WIDGET_ID, "widget-last-prompt", "widget-snapshot", "2026-08-20T04:00:07.000Z", str(cwd),
            "last-prompt", None,
        ),
    ]
    widget_path = root / f"{WIDGET_ID}.jsonl"
    _write_transcript(widget_path, widget)
    # Encrypted per-session state siblings sit beside the transcript and are never read.
    (root / WIDGET_ID / "compression-v2").mkdir(parents=True, exist_ok=True)
    (root / WIDGET_ID / "state.json").write_text('{"enc": "QODER_STATE_DECOY"}', encoding="utf-8")
    (root / WIDGET_ID / "compression-v2" / "state.json").write_text(
        '{"enc": "QODER_COMPACTION_DECOY"}', encoding="utf-8"
    )
    _write_transcript(
        root / f"{GADGET_ID}.jsonl",
        [
            _user(GADGET_ID, "gadget-user", None, "2026-08-20T05:00:00.000Z", str(cwd), "Continue the Qoder gadget."),
            _assistant(
                GADGET_ID, "gadget-assistant", "gadget-user", "2026-08-20T05:00:01.000Z", str(cwd),
                [{"type": "text", "text": "Gadget reply."}],
            ),
        ],
    )
    _write_transcript(
        home / "projects" / _slug(other_cwd) / f"{OTHER_ID}.jsonl",
        [
            _user(OTHER_ID, "other-user", None, "2026-08-20T06:00:00.000Z", str(other_cwd), "QODER_OTHER_WORKSPACE"),
        ],
    )
    # Run-log segment decoy: verbose model-context log, never a transcript source.
    segment = (
        home / "logs" / "sessions" / _slug(cwd) / WIDGET_ID / "segments"
        / "2026-08-20T04-00-07-000-00-00-fixture-p1.jsonl"
    )
    segment.parent.mkdir(parents=True, exist_ok=True)
    segment.write_text(
        json.dumps({"type": "model.response.completed", "data": {"model": "decoy"}}) + "\n",
        encoding="utf-8",
    )
    if ide_root is not None:
        _write_transcript(
            ide_root / f"{IDE_ID}.jsonl",
            [
                _user(IDE_ID, "ide-user", None, "2026-08-20T07:00:00.000Z", str(cwd), "Continue the Qoder IDE fixture."),
                _assistant(
                    IDE_ID, "ide-assistant", "ide-user", "2026-08-20T07:00:01.000Z", str(cwd),
                    [{"type": "text", "text": "Read the IDE transcript."}],
                ),
            ],
        )
    return widget_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--other-cwd", type=Path)
    parser.add_argument("--ide", type=Path)
    args = parser.parse_args()
    cwd = args.cwd.expanduser().resolve()
    other = args.other_cwd.expanduser().resolve() if args.other_cwd else cwd / "other-workspace"
    cwd.mkdir(parents=True, exist_ok=True)
    other.mkdir(parents=True, exist_ok=True)
    ide = args.ide.expanduser().resolve() if args.ide else None
    print(build(args.home.expanduser().resolve(), cwd, other, ide))


if __name__ == "__main__":
    main()

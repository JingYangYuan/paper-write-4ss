#!/usr/bin/env python3
"""Register paper-master-4ss guard hooks into the ZCode user configuration.

ZCode does not execute skill frontmatter hooks; hooks live in
~/.zcode/cli/config.json (disabled until hooks.enabled is true). This script
idempotently registers PostToolUse(Bash) and Stop command hooks pointing at
scripts/paper_master_guard.py, preserving every other configuration key.

Modes:
  (default)  register the hooks (idempotent)
  --check    read-only: exit 0 if both hooks are registered and enabled
  --remove   remove the hooks registered by this script
  --config   target an alternate config file (for testing)

stdout of the guard commands is redirected to /dev/null because ZCode parses
hook stdout as strict-schema JSON; exit codes and stderr stay operative.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
GUARD = PKG_ROOT / "scripts" / "paper_master_guard.py"
DEFAULT_CONFIG = Path.home() / ".zcode" / "cli" / "config.json"
BACKUP_SUFFIX = ".paper-master.bak"

POST_COMMAND = f'python3 "{GUARD}" post-bash --workspace paper-workspace >/dev/null'
STOP_COMMAND = f'python3 "{GUARD}" stop-check --workspace paper-workspace >/dev/null'
POST_MATCHER = "^Bash$"
GUARD_MARK = "paper_master_guard.py"
HOOK_TIMEOUT_MS = 30000


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"无法解析 {path}（{exc}）；为避免破坏配置，本脚本不做任何修改。", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print(f"{path} 顶层不是 JSON 对象；为避免破坏配置，本脚本不做任何修改。", file=sys.stderr)
        sys.exit(1)
    return data


def save_config(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        backup = path.with_name(path.name + BACKUP_SUFFIX)
        shutil.copy2(path, backup)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    return backup


def events_table(data: dict, create: bool) -> dict | None:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        if not create:
            return None
        hooks = {}
        data["hooks"] = hooks
    events = hooks.get("events")
    if not isinstance(events, dict):
        if not create:
            return None
        events = {}
        hooks["events"] = events
    return events


def event_groups(events: dict, name: str, create: bool) -> list | None:
    groups = events.get(name)
    if not isinstance(groups, list):
        if not create:
            return None
        groups = []
        events[name] = groups
    return groups


def find_group(groups: list, matcher: str | None) -> list | None:
    for group in groups:
        if isinstance(group, dict) and group.get("matcher", None) == matcher:
            inner = group.get("hooks")
            if isinstance(inner, list):
                return inner
    return None


def has_our_hook(inner: list, subcommand: str) -> bool:
    for hook in inner:
        if not isinstance(hook, dict):
            continue
        command = hook.get("command", "")
        if GUARD_MARK in str(command) and f" {subcommand} " in f"{command} ":
            return True
    return False


def ensure_hook(groups: list, matcher: str | None, subcommand: str, command: str) -> bool:
    inner = find_group(groups, matcher)
    if inner is None:
        inner = []
        group: dict = {"hooks": inner}
        if matcher is not None:
            group["matcher"] = matcher
        groups.append(group)
    if has_our_hook(inner, subcommand):
        return False
    inner.append({"type": "command", "command": command, "timeoutMs": HOOK_TIMEOUT_MS})
    return True


def strip_our_hooks(groups: list) -> bool:
    changed = False
    for group in groups[:]:
        if not isinstance(group, dict):
            continue
        inner = group.get("hooks")
        if not isinstance(inner, list):
            continue
        kept = [h for h in inner if not (isinstance(h, dict) and GUARD_MARK in str(h.get("command", "")))]
        if len(kept) != len(inner):
            changed = True
        if kept:
            group["hooks"] = kept
        else:
            groups.remove(group)
    return changed


def registered_state(data: dict) -> tuple[bool, bool, bool]:
    enabled = isinstance(data.get("hooks"), dict) and bool(data["hooks"].get("enabled"))
    events = events_table(data, create=False)
    post = stop = False
    if events:
        for group in event_groups(events, "PostToolUse", create=False) or []:
            if isinstance(group, dict) and find_group([group], POST_MATCHER) is not None:
                inner = group.get("hooks") or []
                post = post or has_our_hook(inner, "post-bash")
        for group in event_groups(events, "Stop", create=False) or []:
            if isinstance(group, dict):
                inner = group.get("hooks") or []
                stop = stop or has_our_hook(inner, "stop-check")
    return enabled, post, stop


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只读查询注册状态，不修改配置")
    parser.add_argument("--remove", action="store_true", help="移除本脚本注册的 hooks")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="目标配置文件（默认 ~/.zcode/cli/config.json）")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    data = load_config(config_path)

    if args.check:
        enabled, post, stop = registered_state(data)
        print(f"config: {config_path}")
        print(f"hooks.enabled: {'true' if enabled else 'false/缺失'}")
        print(f"PostToolUse(^Bash$) -> guard post-bash: {'已注册' if post else '未注册'}")
        print(f"Stop -> guard stop-check: {'已注册' if stop else '未注册'}")
        return 0 if (enabled and post and stop) else 1

    if args.remove:
        events = events_table(data, create=False)
        changed = False
        if events:
            for name in ("PostToolUse", "Stop"):
                groups = event_groups(events, name, create=False)
                if groups:
                    changed = strip_our_hooks(groups) or changed
                    if not groups:
                        events.pop(name, None)
            if not events:
                data.get("hooks", {}).pop("events", None)
        if changed:
            backup = save_config(config_path, data)
            if backup:
                print(f"已移除 paper-master guard hooks（备份: {backup}）")
            else:
                print("已移除 paper-master guard hooks")
        else:
            print("未发现可移除的 paper-master guard hooks")
        return 0

    events = events_table(data, create=True)
    changed = False
    changed = ensure_hook(event_groups(events, "PostToolUse", create=True), POST_MATCHER, "post-bash", POST_COMMAND) or changed
    stop_groups = event_groups(events, "Stop", create=True)
    inner = find_group(stop_groups, None) or find_group(stop_groups, "")
    if inner is None:
        changed = ensure_hook(stop_groups, None, "stop-check", STOP_COMMAND) or changed
    else:
        if not has_our_hook(inner, "stop-check"):
            inner.append({"type": "command", "command": STOP_COMMAND, "timeoutMs": HOOK_TIMEOUT_MS})
            changed = True
    hooks = data["hooks"]
    if not hooks.get("enabled"):
        hooks["enabled"] = True
        changed = True

    if changed:
        backup = save_config(config_path, data)
        if backup:
            print(f"已注册 paper-master guard hooks 并启用 hooks.enabled（备份: {backup}）")
        else:
            print("已注册 paper-master guard hooks 并启用 hooks.enabled（新建配置，无原文件可备份）")
        print("注册当次会话请继续显式运行 guard 命令；配置从下一次会话起自动触发。")
    else:
        print("paper-master guard hooks 已是注册状态，无需修改。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

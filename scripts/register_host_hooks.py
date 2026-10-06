#!/usr/bin/env python3
"""Register the paper-master-4ss guard hooks into a host configuration.

Host-agnostic successor of ``register_zcode_hooks.py``. The guard contract is
identical on every host:

* a post-command hook runs ``paper_master_guard.py post-bash`` (pass = 0;
  ``--strict`` makes audit problems exit 2);
* a stop hook runs ``paper_master_guard.py stop-check`` (blocking = 2).

Only the plumbing differs: where the host keeps hook configuration, how events
are nested, what the host calls its shell tool, and whether hook stdout must be
kept clean. Those are described by ``BACKENDS``; hosts without a hook interface
use the manual commands in ``references/hooks-and-evaluation.md`` instead.

Modes:
  (default)          register the hooks for the selected host (idempotent)
  --check            read-only: report whether both hooks are registered
  --remove           remove the hooks registered by this script
  --print            print the host hook snippet and exit without writing
  --strict           include --strict in the registered post-bash command
  --host auto|<name> select the host (default: auto detective rules below)
  --project <dir>    project root for project-scoped hosts (default: cwd)
  --config <file>    override the target configuration file (for testing)

``auto`` only writes when it finds positive evidence for the *current* host:
an explicit environment hint, or a project-local configuration directory. It
never guesses from a home-level configuration of some other host, and it never
writes when no known host is detected.

Safety: writes are append-only, idempotent, and preceded by a
``*.paper-master.bak`` backup. Only the hook keys of the target file are
touched; ``~/.claude.json`` is never read or written.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
GUARD = PKG_ROOT / "scripts" / "paper_master_guard.py"
DEFAULT_WORKSPACE = "paper-workspace"
BACKUP_SUFFIX = ".paper-master.bak"
GUARD_MARK = "paper_master_guard.py"
EVENT_POST = "PostToolUse"
EVENT_STOP = "Stop"


@dataclass(frozen=True)
class Backend:
    """Host hook plumbing."""

    key: str
    label: str
    path: str
    scope: str
    events_path: tuple
    post_matcher: str
    post_wrapped: bool = True
    stop_wrapped: bool = True
    enable_path: tuple = ()
    timeout_key: str = ""
    timeout_value: int = 0
    redirect_stdout: bool = False
    env_keys: tuple = ()
    local_hints: tuple = ()


BACKENDS = (
    Backend(
        key="claude-code",
        label="Claude Code",
        path=".claude/settings.json",
        scope="project",
        events_path=("hooks",),
        post_matcher="Bash",
        env_keys=("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_ROOT", "CLAUDECODE"),
        local_hints=(".claude/settings.json", ".claude"),
    ),
    Backend(
        key="antigravity",
        label="Antigravity",
        path=".agents/hooks.json",
        scope="project",
        events_path=("paper-master-guard",),
        post_matcher="run_command",
        stop_wrapped=False,
        env_keys=("ANTIGRAVITY_HOME", "AGY_HOME", "ANTIGRAVITY_PROJECT_DIR"),
        local_hints=(".agents/hooks.json", ".agents"),
    ),
    Backend(
        key="zcode",
        label="ZCode",
        path="~/.zcode/cli/config.json",
        scope="home",
        events_path=("hooks", "events"),
        post_matcher="^Bash$",
        enable_path=("hooks", "enabled"),
        timeout_key="timeoutMs",
        timeout_value=30000,
        redirect_stdout=True,
        env_keys=("ZCODE_HOME", "ZCODE_CONFIG_DIR", "ZCODE_PROJECT_DIR"),
    ),
)
BACKEND_BY_KEY = {b.key: b for b in BACKENDS}


# --------------------------------------------------------------------------- #
# configuration helpers
# --------------------------------------------------------------------------- #

# 宿主/外层 harness 自带 hook 层的会话标记：这类运行时通过 preset 或平台配置
# 注入 hooks，自动检测不应再往项目或用户目录写第二份宿主配置。只做精确匹配，
# 不做前缀猜测。
HARNESS_OWN_HOOK_KEYS = (
    "DSH_HOME",
    "DSH_SESSION_ID",
    "DSH_PROFILE",
    "DSH_PROFILE_DIR",
)

def get_mapping(root: dict, path: tuple, create: bool):
    node = root
    for key in path:
        nxt = node.get(key)
        if not isinstance(nxt, dict):
            if not create:
                return None
            nxt = {}
            node[key] = nxt
        node = nxt
    return node


def get_value(root: dict, path: tuple):
    if not path:
        return None
    node = get_mapping(root, path[:-1], create=False)
    if not isinstance(node, dict):
        return None
    return node.get(path[-1])


def set_value(root: dict, path: tuple, value) -> None:
    node = get_mapping(root, path[:-1], create=True)
    node[path[-1]] = value


def get_events(data: dict, backend: Backend, create: bool):
    return get_mapping(data, backend.events_path, create)


def event_groups(events: dict, name: str, create: bool):
    groups = events.get(name)
    if not isinstance(groups, list):
        if not create:
            return None
        groups = []
        events[name] = groups
    return groups


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


def save_config(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        backup = path.with_name(path.name + BACKUP_SUFFIX)
        shutil.copy2(path, backup)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return backup


def is_ours(entry) -> bool:
    return isinstance(entry, dict) and GUARD_MARK in str(entry.get("command", ""))


def has_our_hook(entries, subcommand: str) -> bool:
    for entry in entries:
        if is_ours(entry) and f" {subcommand} " in f"{entry.get('command', '')} ":
            return True
    return False


def iter_hook_entries(groups):
    """Yield ``(matcher, entry)`` for wrapped groups and flat hook lists."""
    for group in groups:
        if not isinstance(group, dict):
            continue
        inner = group.get("hooks")
        if isinstance(inner, list):
            for entry in inner:
                yield group.get("matcher", None), entry
        elif "command" in group:
            yield group.get("matcher", None), group


def find_wrapped(groups, matcher: str):
    for group in groups:
        if isinstance(group, dict) and group.get("matcher", None) == matcher:
            inner = group.get("hooks")
            if isinstance(inner, list):
                return inner
    return None


def hook_entry(backend: Backend, command: str) -> dict:
    entry = {"type": "command", "command": command}
    if backend.timeout_key:
        entry[backend.timeout_key] = backend.timeout_value
    return entry


def ensure_wrapped(backend: Backend, groups: list, matcher: str, subcommand: str, command: str) -> bool:
    inner = find_wrapped(groups, matcher)
    if inner is None:
        inner = []
        groups.append({"matcher": matcher, "hooks": inner})
    if has_our_hook(inner, subcommand):
        return False
    inner.append(hook_entry(backend, command))
    return True


def ensure_flat(backend: Backend, groups: list, subcommand: str, command: str) -> bool:
    if has_our_hook(iter_hook_entries(groups), subcommand):
        return False
    groups.append(hook_entry(backend, command))
    return True


def strip_our_hooks(groups) -> bool:
    changed = False
    for group in groups[:]:
        if not isinstance(group, dict):
            continue
        inner = group.get("hooks")
        if isinstance(inner, list):
            kept = [h for h in inner if not is_ours(h)]
            if len(kept) != len(inner):
                changed = True
            if kept:
                group["hooks"] = kept
            else:
                groups.remove(group)
        elif is_ours(group):
            groups.remove(group)
            changed = True
    return changed


def registered_state(data: dict, backend: Backend):
    if backend.enable_path:
        enabled = bool(get_value(data, backend.enable_path))
    else:
        enabled = True
    post = stop = False
    post_matcher = None
    events = get_events(data, backend, create=False)
    if isinstance(events, dict):
        groups = event_groups(events, EVENT_POST, create=False) or []
        for matcher, entry in iter_hook_entries(groups):
            if is_ours(entry) and " post-bash " in f"{entry.get('command', '')} ":
                if matcher == backend.post_matcher:
                    post = True
                    post_matcher = matcher
                elif post_matcher is None:
                    post_matcher = matcher
        stop_groups = event_groups(events, EVENT_STOP, create=False) or []
        stop = has_our_hook((entry for _, entry in iter_hook_entries(stop_groups)), "stop-check")
    return enabled, post, stop, post_matcher


# --------------------------------------------------------------------------- #
# host selection
# --------------------------------------------------------------------------- #

def project_root(arg: str) -> Path:
    return Path(arg).expanduser().resolve()


def resolve_config(backend: Backend, project: Path, override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    if backend.scope == "home":
        return Path(backend.path).expanduser()
    return project / backend.path


def detect_host(project: Path, note) -> str | None:
    """Detect the current host from exact environment markers or project config.

    Exact names only: broad prefixes misfire (for example a globally exported
    ``CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE`` says nothing about the host that
    is running this skill). When nothing is found, nothing is written.
    """
    env = os.environ
    for key in HARNESS_OWN_HOOK_KEYS:
        if env.get(key):
            note(f"检测到 {key}：当前运行时自带 hook 层（preset/平台配置），"
                 "自动模式不写任何文件；如需本包 guard，请用 --host <name> 显式指定，"
                 "或继续显式运行两条 guard 命令")
            return None
    for backend in BACKENDS:
        for key in backend.env_keys:
            if env.get(key):
                note(f"环境变量 {key} 指向 {backend.label}")
                return backend.key
    for backend in BACKENDS:
        if backend.scope != "project":
            continue
        for hint in backend.local_hints:
            if (project / hint).exists():
                note(f"项目内存在 {hint}")
                return backend.key
    return None


def guard_command(backend: Backend, subcommand: str, workspace: str, strict: bool) -> str:
    command = f'python3 "{GUARD}" {subcommand} --workspace {workspace}'
    if subcommand == "post-bash" and strict:
        command += " --strict"
    if backend.redirect_stdout:
        command += " >/dev/null"
    return command


def snippet(backend: Backend, workspace: str, strict: bool) -> str:
    """Render the hook snippet for a backend as pasteable JSON."""
    post_entry = hook_entry(backend, guard_command(backend, "post-bash", workspace, strict))
    stop_entry = hook_entry(backend, guard_command(backend, "stop-check", workspace, strict))
    events: dict = {}
    if backend.post_wrapped:
        events[EVENT_POST] = [{"matcher": backend.post_matcher, "hooks": [post_entry]}]
    else:
        events[EVENT_POST] = [post_entry]
    if backend.stop_wrapped:
        events[EVENT_STOP] = [{"matcher": "", "hooks": [stop_entry]}]
    else:
        events[EVENT_STOP] = [stop_entry]

    wrapper: dict = {}
    node = wrapper
    for key in backend.events_path[:-1]:
        node[key] = {}
        node = node[key]
    node[backend.events_path[-1]] = events
    if backend.enable_path:
        enode = wrapper
        for key in backend.enable_path[:-1]:
            enode = enode.setdefault(key, {})
        enode[backend.enable_path[-1]] = True
    return json.dumps(wrapper, ensure_ascii=False, indent=2)


GENERIC_CONTRACT = """通用 hook 契约（宿主自定 JSON 形状）：

  PostToolUse / 命令执行后（matcher = 该宿主的 shell 工具名，如 Bash、run_command）
    python3 "{guard}" post-bash --workspace {workspace}
  Stop / 会话结束前
    python3 "{guard}" stop-check --workspace {workspace}

约定：
  * post-bash 通过 = 退出码 0；加 --strict 时审计问题 = 退出码 2；Stop 阻断 = 退出码 2；
  * 若宿主把 hook stdout 当作严格 JSON 解析，请在命令后追加 >/dev/null，只保留退出码与 stderr；
  * 命令需用本包绝对路径，或宿主提供的插件根变量；无 paper-workspace/ 时 guard 静默退出。
  * 宿主已有自己的 hook 机制（插件 preset、平台配置）时，优先用宿主机制，不必运行本脚本。
""".format(guard=GUARD, workspace=DEFAULT_WORKSPACE)


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_print(backend: Backend | None, workspace: str, strict: bool) -> int:
    if backend is None:
        print(GENERIC_CONTRACT)
        return 0
    print(f"# {backend.label}（{backend.key}）hook 片段")
    print(f"# 目标文件：{backend.path}")
    print(snippet(backend, workspace, strict))
    print()
    print(GENERIC_CONTRACT)
    return 0


def cmd_check(backend: Backend, config_path: Path, as_json: bool) -> int:
    data = load_config(config_path)
    enabled, post, stop, matcher = registered_state(data, backend)
    registered = bool(enabled and post and stop)
    if as_json:
        print(json.dumps({
            "host": backend.key,
            "config": str(config_path),
            "config_exists": config_path.exists(),
            "enabled": enabled,
            "post": post,
            "post_matcher": matcher,
            "stop": stop,
            "registered": registered,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"host: {backend.label} ({backend.key})")
        print(f"config: {config_path}")
        if backend.enable_path:
            print(f"hooks.enabled: {'true' if enabled else 'false/缺失'}")
        print(f"{EVENT_POST}({backend.post_matcher}) -> guard post-bash: {'已注册' if post else '未注册'}")
        print(f"{EVENT_STOP} -> guard stop-check: {'已注册' if stop else '未注册'}")
    return 0 if registered else 1


def cmd_remove(backend: Backend, config_path: Path) -> int:
    if not config_path.exists():
        print(f"未发现配置文件 {config_path}，无需移除。")
        return 0
    data = load_config(config_path)
    events = get_events(data, backend, create=False)
    changed = False
    if isinstance(events, dict):
        for name in (EVENT_POST, EVENT_STOP):
            groups = event_groups(events, name, create=False)
            if groups:
                changed = strip_our_hooks(groups) or changed
                if not groups:
                    events.pop(name, None)
    if changed:
        backup = save_config(config_path, data)
        print(f"已移除 {backend.label} 的 paper-master guard hooks（备份: {backup}）" if backup
              else f"已移除 {backend.label} 的 paper-master guard hooks")
    else:
        print(f"未发现可移除的 {backend.label} paper-master guard hooks")
    return 0


def cmd_register(backend: Backend, config_path: Path, workspace: str, strict: bool) -> int:
    data = load_config(config_path)
    events = get_events(data, backend, create=True)
    changed = False
    post_command = guard_command(backend, "post-bash", workspace, strict)
    stop_command = guard_command(backend, "stop-check", workspace, strict)
    groups = event_groups(events, EVENT_POST, create=True)
    if backend.post_wrapped:
        changed = ensure_wrapped(backend, groups, backend.post_matcher, "post-bash", post_command) or changed
    else:
        changed = ensure_flat(backend, groups, "post-bash", post_command) or changed

    stop_groups = event_groups(events, EVENT_STOP, create=True)
    if backend.stop_wrapped:
        inner = find_wrapped(stop_groups, None) or find_wrapped(stop_groups, "")
        if inner is None:
            inner = []
            stop_groups.append({"matcher": "", "hooks": inner})
        if not has_our_hook(inner, "stop-check"):
            inner.append(hook_entry(backend, stop_command))
            changed = True
    else:
        changed = ensure_flat(backend, stop_groups, "stop-check", stop_command) or changed

    if backend.enable_path and not get_value(data, backend.enable_path):
        set_value(data, backend.enable_path, True)
        changed = True

    if changed:
        backup = save_config(config_path, data)
        if backup:
            print(f"已为 {backend.label} 注册 paper-master guard hooks（备份: {backup}）")
        else:
            print(f"已为 {backend.label} 注册 paper-master guard hooks（新建配置，无原文件可备份）")
        print("注册当次会话请继续显式运行 guard 命令；配置从下一次会话起自动触发。")
    else:
        print(f"{backend.label} 的 paper-master guard hooks 已是注册状态，无需修改。")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="auto",
                        help="auto（默认）或宿主键：%s" % "、".join(BACKEND_BY_KEY))
    parser.add_argument("--check", action="store_true", help="只读查询注册状态，不修改配置")
    parser.add_argument("--remove", action="store_true", help="移除本脚本注册的 hooks")
    parser.add_argument("--print", dest="print_only", action="store_true",
                        help="打印该宿主的 hook 片段，不修改任何文件")
    parser.add_argument("--strict", action="store_true",
                        help="注册的 post-bash 命令附带 --strict（审计问题退出码 2）")
    parser.add_argument("--project", default=".", help="项目根目录（项目级宿主用，默认当前目录）")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, help="传给 guard 的 --workspace")
    parser.add_argument("--config", default=None, help="目标配置文件（覆盖宿主默认路径，仅用于测试）")
    parser.add_argument("--json", action="store_true", help="--check 以 JSON 输出")
    args = parser.parse_args(argv)

    project = project_root(args.project)
    notes: list[str] = []
    host = args.host
    if host == "auto":
        host = detect_host(project, notes.append)
    if host is not None and host not in BACKEND_BY_KEY:
        print(f"未知宿主 {host}；可用：{', '.join(BACKEND_BY_KEY)}", file=sys.stderr)
        return 2
    backend = BACKEND_BY_KEY[host] if host else None
    for note in notes:
        print(f"[auto] {note}")

    if args.print_only:
        return cmd_print(backend, args.workspace, args.strict)

    if backend is None:
        print("未能判定当前宿主；未修改任何文件。可用 --host <name> 指定，或直接采用下面的片段：",
              file=sys.stderr)
        print(GENERIC_CONTRACT)
        return 2

    config_path = resolve_config(backend, project, args.config)
    if args.check:
        return cmd_check(backend, config_path, args.json)
    if args.remove:
        return cmd_remove(backend, config_path)
    return cmd_register(backend, config_path, args.workspace, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())

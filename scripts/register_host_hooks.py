#!/usr/bin/env python3
"""Register the paper-master-4ss guard hooks into the current agent host.

The guard contract is identical on every host:

* a post-command hook runs ``paper_master_guard.py post-bash`` (pass = 0;
  ``--strict`` makes audit problems exit 2);
* a stop hook runs ``paper_master_guard.py stop-check`` (blocking = 2).

Only the plumbing differs: where the host keeps hook configuration, how the
events are nested, and what the host calls its shell tool. Those three facts
are not guessed here. On first use the script runs a short wizard: you pick the
configuration file (``--detect`` lists candidates first), the hook shape, and
the matcher name; the answer is stored as a profile and reused afterwards.

Shapes (see ``references/agent-software-adapters.md`` §2 for the JSON):

  A  project-level file, ``hooks.<PostEvent>`` and ``hooks.Stop`` each wrap a
     ``hooks`` array with a matcher.
  B  user-level file, events under ``hooks.events`` plus an ``enabled`` switch,
     hook stdout usually suppressed.
  C  project-level file, a namespace block whose post event wraps a ``hooks``
     array and whose stop event is a flat list.

Modes:
  --setup    run the wizard and store the profile (then register)
  --detect   read-only: list JSON files that look like hook configuration
  (default)  register the hooks described by the profile (idempotent)
  --check    read-only: report whether both hooks are registered
  --remove   remove the hooks registered by this script
  --print    print the hook snippet and exit without writing
  --strict   include --strict in the registered post-bash command

Safety: writes are append-only, idempotent, and preceded by a
``*.paper-master.bak`` backup. Only the hook keys of the target file are
touched. A file that cannot be parsed is left untouched.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
GUARD = PKG_ROOT / "scripts" / "paper_master_guard.py"
DEFAULT_WORKSPACE = "paper-workspace"
BACKUP_SUFFIX = ".paper-master.bak"
GUARD_MARK = "paper_master_guard.py"
PROFILE_DIR = ".paper-master"
PROFILE_NAME = "host-profile.json"

POST_DEFAULT = "PostToolUse"
STOP_DEFAULT = "Stop"
DEFAULT_MATCHER = "Bash"

# 形状只描述嵌套方式，不描述软件。字段含义见模块 docstring。
SHAPES: dict[str, dict] = {
    "A": {
        "events_path": ["hooks"],
        "wrapped_post": True,
        "wrapped_stop": True,
        "enable_path": [],
        "timeout_ms": 0,
        "redirect_stdout": False,
        "label": "项目级：hooks 下的事件各包一层 hooks 数组",
    },
    "B": {
        "events_path": ["hooks", "events"],
        "wrapped_post": True,
        "wrapped_stop": True,
        "enable_path": ["hooks", "enabled"],
        "timeout_ms": 30000,
        "redirect_stdout": True,
        "label": "用户级：hooks.events 下挂事件，另有 enabled 开关",
    },
    "C": {
        "events_path": ["paper-master-guard"],
        "wrapped_post": True,
        "wrapped_stop": False,
        "enable_path": [],
        "timeout_ms": 0,
        "redirect_stdout": False,
        "label": "项目级：命名空间块，Stop 事件为扁平列表",
    },
}


@dataclass
class Profile:
    """Where the hooks go and how they are nested."""

    config: Path
    shape: str = "A"
    events_path: tuple = ("hooks",)
    wrapped_post: bool = True
    wrapped_stop: bool = True
    enable_path: tuple = ()
    timeout_ms: int = 0
    redirect_stdout: bool = False
    matcher: str = DEFAULT_MATCHER
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "config": str(self.config),
            "shape": self.shape,
            "events_path": list(self.events_path),
            "wrapped_post": self.wrapped_post,
            "wrapped_stop": self.wrapped_stop,
            "enable_path": list(self.enable_path),
            "timeout_ms": self.timeout_ms,
            "redirect_stdout": self.redirect_stdout,
            "matcher": self.matcher,
        }

    @classmethod
    def from_shape(cls, config: Path, shape: str, matcher: str, redirect: bool | None) -> "Profile":
        spec = SHAPES.get(shape.upper())
        if spec is None:
            raise SystemExit(f"未知形状 {shape}；可用：{', '.join(SHAPES)}")
        return cls(
            config=config,
            shape=shape.upper(),
            events_path=tuple(spec["events_path"]),
            wrapped_post=bool(spec["wrapped_post"]),
            wrapped_stop=bool(spec["wrapped_stop"]),
            enable_path=tuple(spec["enable_path"]),
            timeout_ms=int(spec["timeout_ms"]),
            redirect_stdout=bool(spec["redirect_stdout"]) if redirect is None else redirect,
            matcher=matcher,
        )

    @classmethod
    def load(cls, path: Path) -> "Profile | None":
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"无法解析 profile {path}（{exc}）；请重跑 --setup。", file=sys.stderr)
            return None
        if not isinstance(data, dict) or not data.get("config"):
            print(f"profile {path} 缺少 config 字段；请重跑 --setup。", file=sys.stderr)
            return None
        return cls(
            config=Path(str(data["config"])).expanduser(),
            shape=str(data.get("shape", "A")).upper(),
            events_path=tuple(data.get("events_path") or ("hooks",)),
            wrapped_post=bool(data.get("wrapped_post", True)),
            wrapped_stop=bool(data.get("wrapped_stop", True)),
            enable_path=tuple(data.get("enable_path") or ()),
            timeout_ms=int(data.get("timeout_ms") or 0),
            redirect_stdout=bool(data.get("redirect_stdout", False)),
            matcher=str(data.get("matcher") or DEFAULT_MATCHER),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# configuration helpers
# --------------------------------------------------------------------------- #

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


def get_events(data: dict, profile: Profile, create: bool):
    return get_mapping(data, profile.events_path, create)


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
        import shutil

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


def find_wrapped(groups, matcher):
    for group in groups:
        if isinstance(group, dict) and group.get("matcher", None) == matcher:
            inner = group.get("hooks")
            if isinstance(inner, list):
                return inner
    return None


def hook_entry(profile: Profile, command: str) -> dict:
    entry = {"type": "command", "command": command}
    if profile.timeout_ms:
        entry["timeoutMs"] = profile.timeout_ms
    return entry


def ensure_wrapped(profile: Profile, groups: list, matcher: str, subcommand: str, command: str) -> bool:
    inner = find_wrapped(groups, matcher)
    if inner is None:
        inner = []
        groups.append({"matcher": matcher, "hooks": inner})
    if has_our_hook(inner, subcommand):
        return False
    inner.append(hook_entry(profile, command))
    return True


def ensure_flat(profile: Profile, groups: list, subcommand: str, command: str) -> bool:
    if has_our_hook(iter_hook_entries(groups), subcommand):
        return False
    groups.append(hook_entry(profile, command))
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


def registered_state(data: dict, profile: Profile):
    if profile.enable_path:
        enabled = bool(get_value(data, profile.enable_path))
    else:
        enabled = True
    post = stop = False
    post_matcher = None
    events = get_events(data, profile, create=False)
    if isinstance(events, dict):
        groups = event_groups(events, POST_DEFAULT, create=False) or []
        for matcher, entry in iter_hook_entries(groups):
            if is_ours(entry) and " post-bash " in f"{entry.get('command', '')} ":
                if matcher == profile.matcher:
                    post = True
                    post_matcher = matcher
                elif post_matcher is None:
                    post_matcher = matcher
        stop_groups = event_groups(events, STOP_DEFAULT, create=False) or []
        stop = has_our_hook((entry for _, entry in iter_hook_entries(stop_groups)), "stop-check")
    return enabled, post, stop, post_matcher


def guard_command(profile: Profile, subcommand: str, workspace: str, strict: bool) -> str:
    command = f'python3 "{GUARD}" {subcommand} --workspace {workspace}'
    if subcommand == "post-bash" and strict:
        command += " --strict"
    if profile.redirect_stdout:
        command += " >/dev/null"
    return command


def snippet(profile: Profile, workspace: str, strict: bool) -> str:
    """Render the hook snippet for a profile as pasteable JSON."""
    post_entry = hook_entry(profile, guard_command(profile, "post-bash", workspace, strict))
    stop_entry = hook_entry(profile, guard_command(profile, "stop-check", workspace, strict))
    events: dict = {}
    if profile.wrapped_post:
        events[POST_DEFAULT] = [{"matcher": profile.matcher, "hooks": [post_entry]}]
    else:
        events[POST_DEFAULT] = [post_entry]
    if profile.wrapped_stop:
        events[STOP_DEFAULT] = [{"matcher": "", "hooks": [stop_entry]}]
    else:
        events[STOP_DEFAULT] = [stop_entry]

    wrapper: dict = {}
    node = wrapper
    for key in profile.events_path[:-1]:
        node[key] = {}
        node = node[key]
    node[profile.events_path[-1]] = events
    if profile.enable_path:
        enode = wrapper
        for key in profile.enable_path[:-1]:
            enode = enode.setdefault(key, {})
        enode[profile.enable_path[-1]] = True
    return json.dumps(wrapper, ensure_ascii=False, indent=2)


GENERIC_CONTRACT = """通用 hook 契约（宿主自定 JSON 形状）：

  PostToolUse / 命令执行后（matcher = 该宿主的 shell 工具名）
    python3 "{guard}" post-bash --workspace {workspace}
  Stop / 会话结束前
    python3 "{guard}" stop-check --workspace {workspace}

约定：
  * post-bash 通过 = 退出码 0；加 --strict 时审计问题 = 退出码 2；Stop 阻断 = 退出码 2；
  * 若宿主把 hook stdout 当作严格 JSON 解析，请在命令后追加 >/dev/null，只保留退出码与 stderr；
  * 命令需用本包绝对路径，或宿主提供的插件根变量；无 paper-workspace/ 时 guard 静默退出。
  * 宿主已有自己的 hook 机制（插件 preset、平台配置）时，优先用宿主机制，不必运行本脚本。

要自动注册：先跑 --detect 找配置，再跑 --setup 走向导，答案存进 .paper-master/host-profile.json。
""".format(guard=GUARD, workspace=DEFAULT_WORKSPACE)


# --------------------------------------------------------------------------- #
# discovery + wizard
# --------------------------------------------------------------------------- #

def detect_candidates(project: Path, limit: int = 12) -> list[Path]:
    """List JSON files that contain a top-level ``hooks`` key.

    Pure shape detection: no host names, no fixed paths. Project tree first
    (depth-limited), then dot-directories in the home folder.
    """
    found: list[Path] = []
    seen: set[Path] = set()

    def consider(path: Path) -> None:
        if path in seen or not path.is_file() or not path.name.endswith(".json"):
            return
        seen.add(path)
        try:
            if path.stat().st_size > 512 * 1024:
                return
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        if "hooks" in data or any(isinstance(v, dict) and "PostToolUse" in v for v in data.values()):
            found.append(path)

    def walk(base: Path, depth: int) -> None:
        if depth < 0 or not base.is_dir():
            return
        try:
            entries = list(base.iterdir())
        except OSError:
            return
        for entry in entries:
            if entry.name in {"node_modules", ".git", "__pycache__", "paper-workspace"}:
                continue
            if entry.is_dir():
                walk(entry, depth - 1)
            else:
                consider(entry)

    walk(project, 3)
    project_hits = list(found)
    home = Path.home()
    try:
        dot_dirs = [d for d in home.iterdir() if d.is_dir() and d.name.startswith(".")]
    except OSError:
        dot_dirs = []
    for dot in dot_dirs:
        if dot.name in {".git", ".cache", ".npm", ".conda"}:
            continue
        walk(dot, 2)
        if len(found) >= limit:
            break
    # 项目内的排前面
    found.sort(key=lambda p: (0 if p in project_hits else 1, str(p)))
    return found[:limit]


def _ask(prompt: str, default: str = "") -> str | None:
    """Prompt once. Returns None when stdin is not interactive."""
    if not sys.stdin.isatty():
        return None
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    return answer or default


def run_setup(project: Path, profile_path: Path, args) -> Profile | None:
    """Interactive wizard: pick config file, shape, matcher; persist the profile."""
    config = Path(args.config).expanduser() if args.config else None
    if config is None:
        candidates = detect_candidates(project)
        if candidates:
            print("发现这些像 hook 配置的文件：")
            for i, path in enumerate(candidates, 1):
                print(f"  {i}. {path}")
        else:
            print("没有自动找到 hook 配置；请直接给出目标配置文件的路径。")
        print("宿主通常把自己放在项目内（如 <项目>/.某目录/settings.json）或用户主目录下的点目录里。")
        raw = _ask("选择编号或输入配置文件路径（留空=退出）", "")
        if raw is None:
            print("当前不是交互终端；用 --config <file> --shape A|B|C 直接给出参数。", file=sys.stderr)
            return None
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(candidates):
            config = candidates[int(raw) - 1]
        else:
            config = Path(raw).expanduser()
    if not config.is_absolute():
        config = (project / config).resolve()

    shape = (args.shape or "").upper()
    if not shape:
        print("\n钩子事件的嵌套方式：")
        for key, spec in SHAPES.items():
            print(f"  {key}. {spec['label']}")
        print("  形状说明见 references/agent-software-adapters.md §2；不确定就选 A 并先跑 --print 核对。")
        shape = (_ask("选择形状", "A") or "A").upper()
    if shape not in SHAPES:
        print(f"未知形状 {shape}；可用：{', '.join(SHAPES)}", file=sys.stderr)
        return None

    matcher = args.matcher
    if matcher is None:
        matcher = _ask("\n该宿主的 shell 工具在 matcher 里叫什么（填工具名或正则）", DEFAULT_MATCHER)
        if matcher is None:
            return None

    redirect = args.quiet_stdout
    if redirect is None:
        default_redirect = "y" if SHAPES[shape]["redirect_stdout"] else "n"
        answer = _ask("\n宿主是否把 hook 的 stdout 按严格 JSON 解析（y=命令尾部加 >/dev/null）", default_redirect)
        if answer is None:
            return None
        redirect = answer.lower().startswith("y")

    profile = Profile.from_shape(config, shape, matcher, redirect)
    profile.save(profile_path)
    print(f"\n已写入 profile：{profile_path}")
    print(f"  配置文件：{profile.config}")
    print(f"  形状：{profile.shape}  事件路径：{'.'.join(profile.events_path)}  matcher：{profile.matcher}")
    return profile


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_detect(project: Path) -> int:
    candidates = detect_candidates(project)
    if not candidates:
        print("没有找到含 hooks 键的 JSON 配置；用 --config <file> 直接指定。")
        return 1
    for path in candidates:
        print(path)
    return 0


def cmd_print(profile: Profile | None, workspace: str, strict: bool) -> int:
    if profile is None:
        print(GENERIC_CONTRACT)
        return 0
    print(f"# 形状 {profile.shape}  hook 片段")
    print(f"# 目标文件：{profile.config}")
    print(snippet(profile, workspace, strict))
    print()
    print(GENERIC_CONTRACT)
    return 0


def cmd_check(profile: Profile, as_json: bool) -> int:
    data = load_config(profile.config)
    enabled, post, stop, matcher = registered_state(data, profile)
    registered = bool(enabled and post and stop)
    if as_json:
        print(json.dumps({
            "shape": profile.shape,
            "config": str(profile.config),
            "config_exists": profile.config.exists(),
            "enabled": enabled,
            "post": post,
            "post_matcher": matcher,
            "stop": stop,
            "registered": registered,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"shape: {profile.shape}  config: {profile.config}")
        if profile.enable_path:
            print(f"{'.'.join(profile.enable_path)}: {'true' if enabled else 'false/缺失'}")
        print(f"{POST_DEFAULT}({profile.matcher}) -> guard post-bash: {'已注册' if post else '未注册'}")
        print(f"{STOP_DEFAULT} -> guard stop-check: {'已注册' if stop else '未注册'}")
    return 0 if registered else 1


def cmd_remove(profile: Profile) -> int:
    if not profile.config.exists():
        print(f"未发现配置文件 {profile.config}，无需移除。")
        return 0
    data = load_config(profile.config)
    events = get_events(data, profile, create=False)
    changed = False
    if isinstance(events, dict):
        for name in (POST_DEFAULT, STOP_DEFAULT):
            groups = event_groups(events, name, create=False)
            if groups:
                changed = strip_our_hooks(groups) or changed
                if not groups:
                    events.pop(name, None)
    if changed:
        backup = save_config(profile.config, data)
        print(f"已移除 paper-master guard hooks（备份: {backup}）" if backup
              else "已移除 paper-master guard hooks")
    else:
        print("未发现可移除的 paper-master guard hooks")
    return 0


def cmd_register(profile: Profile, workspace: str, strict: bool) -> int:
    data = load_config(profile.config)
    events = get_events(data, profile, create=True)
    changed = False
    post_command = guard_command(profile, "post-bash", workspace, strict)
    stop_command = guard_command(profile, "stop-check", workspace, strict)
    groups = event_groups(events, POST_DEFAULT, create=True)
    if profile.wrapped_post:
        changed = ensure_wrapped(profile, groups, profile.matcher, "post-bash", post_command) or changed
    else:
        changed = ensure_flat(profile, groups, "post-bash", post_command) or changed

    stop_groups = event_groups(events, STOP_DEFAULT, create=True)
    if profile.wrapped_stop:
        inner = find_wrapped(stop_groups, "") if find_wrapped(stop_groups, "") is not None else find_wrapped(stop_groups, None)
        if inner is None:
            inner = []
            stop_groups.append({"matcher": "", "hooks": inner})
        if not has_our_hook(inner, "stop-check"):
            inner.append(hook_entry(profile, stop_command))
            changed = True
    else:
        changed = ensure_flat(profile, stop_groups, "stop-check", stop_command) or changed

    if profile.enable_path and not get_value(data, profile.enable_path):
        set_value(data, profile.enable_path, True)
        changed = True

    if changed:
        backup = save_config(profile.config, data)
        if backup:
            print(f"已注册 paper-master guard hooks（备份: {backup}）")
        else:
            print("已注册 paper-master guard hooks（新建配置，无原文件可备份）")
        print("注册当次会话请继续显式运行 guard 命令；配置从下一次会话起自动触发。")
    else:
        print("paper-master guard hooks 已是注册状态，无需修改。")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--setup", action="store_true", help="运行向导，选择配置文件与 hook 形状并保存 profile")
    parser.add_argument("--detect", action="store_true", help="只读：列出目录树里像 hook 配置的 JSON")
    parser.add_argument("--check", action="store_true", help="只读查询注册状态，不修改配置")
    parser.add_argument("--remove", action="store_true", help="移除本脚本注册的 hooks")
    parser.add_argument("--print", dest="print_only", action="store_true",
                        help="打印 hook 片段，不修改任何文件")
    parser.add_argument("--strict", action="store_true",
                        help="注册的 post-bash 命令附带 --strict（审计问题退出码 2）")
    parser.add_argument("--project", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, help="传给 guard 的 --workspace")
    parser.add_argument("--profile", default=None, help="profile 路径（默认 <项目>/.paper-master/host-profile.json）")
    parser.add_argument("--config", default=None, help="目标配置文件（向导里跳过路径询问）")
    parser.add_argument("--shape", default=None, choices=["A", "B", "C", "a", "b", "c"],
                        help="hook 形状（向导里跳过形状询问）")
    parser.add_argument("--matcher", default=None, help="matcher 名（向导里跳过询问）")
    parser.add_argument("--quiet-stdout", dest="quiet_stdout", action="store_true", default=None,
                        help="hook 命令尾部加 >/dev/null")
    parser.add_argument("--no-quiet-stdout", dest="quiet_stdout", action="store_false",
                        help="hook 命令尾部不加 >/dev/null")
    parser.add_argument("--json", action="store_true", help="--check 以 JSON 输出")
    args = parser.parse_args(argv)

    project = Path(args.project).expanduser().resolve()
    profile_path = (Path(args.profile).expanduser() if args.profile
                    else project / PROFILE_DIR / PROFILE_NAME)

    if args.detect:
        return cmd_detect(project)

    profile = Profile.load(profile_path)

    if args.setup or (profile is None and not args.print_only and args.config):
        profile = run_setup(project, profile_path, args)
        if profile is None:
            print("\n未完成配置；未修改任何文件。可用的通用片段：", file=sys.stderr)
            print(GENERIC_CONTRACT, file=sys.stderr)
            return 2

    if args.print_only:
        return cmd_print(profile, args.workspace, args.strict)

    if profile is None:
        print(f"未找到 profile {profile_path}。", file=sys.stderr)
        print("首次使用：先跑 --detect 看候选配置，再跑 --setup 走向导。未修改任何文件。", file=sys.stderr)
        print(GENERIC_CONTRACT, file=sys.stderr)
        return 2

    if args.check:
        return cmd_check(profile, args.json)
    if args.remove:
        return cmd_remove(profile)
    return cmd_register(profile, args.workspace, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())

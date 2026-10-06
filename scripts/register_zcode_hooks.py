#!/usr/bin/env python3
"""Register the paper-master-4ss guard hooks into the ZCode configuration.

Backwards-compatible shim: this script is kept so that existing instructions,
standalone packages and bookmarks continue to work. It forwards to
``register_host_hooks.py --host zcode``, which holds the host-agnostic logic.

ZCode does not execute skill frontmatter hooks; hooks live in
~/.zcode/cli/config.json (disabled until hooks.enabled is true). Registration is
idempotent, backed up before writing, append-only, and keeps every other
configuration key. stdout of the guard commands is redirected to /dev/null
because ZCode parses hook stdout as strict-schema JSON; exit codes and stderr
stay operative.

Usage is unchanged, including ``--check``, ``--remove`` and ``--config``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from register_host_hooks import main  # noqa: E402  (path must be set first)


if __name__ == "__main__":
    raise SystemExit(main(["--host", "zcode", *sys.argv[1:]]))

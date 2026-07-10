#!/usr/bin/env python3
"""Amazing Hand の統合 CLI。

使い方:
  uv run hand demo
  uv run hand gesture open
  uv run hand ai
  uv run hand ports
"""

from __future__ import annotations

import importlib
import sys

COMMANDS: dict[str, tuple[str, str]] = {
    "check": ("demo.check", "接続・サーボ応答を確認する"),
    "demo": ("demo.demo", "ジェスチャーデモを繰り返す"),
    "gesture": ("demo.gesture", "ジェスチャーを指定 / 対話実行"),
    "idle": ("demo.idle", "安全な小動作でアイドリング"),
    "calibrate": ("demo.calibrate", "指テスト / 中立位置合わせ"),
    "ports": ("demo.list_ports", "シリアルポート一覧"),
    "ai": ("ai.main", "音声指示で手を動かす"),
}


def usage() -> None:
    print("使い方: hand <command> [options]")
    print()
    print("commands:")
    width = max(len(name) for name in COMMANDS)
    for name, (_, desc) in COMMANDS.items():
        print(f"  {name:<{width}}  {desc}")
    print()
    print("例:")
    print("  hand check")
    print("  hand check --move")
    print("  hand demo --once")
    print("  hand gesture open")
    print("  hand ai --port /dev/tty.usbmodemXXXX")
    print("  hand ports")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        usage()
        return 0 if len(sys.argv) > 1 else 1

    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"不明なコマンド: {command}", file=sys.stderr)
        print(f"候補: {', '.join(COMMANDS)}", file=sys.stderr)
        return 1

    module_name, _ = COMMANDS[command]
    # サブコマンド側の argparse が argv[0] 以降を読むので差し替える
    sys.argv = [f"hand {command}", *sys.argv[2:]]
    module = importlib.import_module(module_name)
    result = module.main()
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())

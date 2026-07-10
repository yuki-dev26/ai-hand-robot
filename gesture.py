#!/usr/bin/env python3
"""対話的にジェスチャーを指定して動かす CLI。

使い方:
  python gesture.py
  python gesture.py --port /dev/tty.usbmodemXXXX open
  python gesture.py close
"""

from __future__ import annotations

import argparse
import sys
import time

from hand import AmazingHand
from ports import find_servo_port

GESTURES = {
    "open": ("開く", "open"),
    "close": ("握る", "close"),
    "middle": ("中立", "middle"),
    "spread": ("広げる", "spread"),
    "point": ("指差し", "point"),
    "victory": ("ピース", "victory"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Amazing Hand ジェスチャー CLI")
    parser.add_argument("--port", default=None, help="シリアルポート")
    parser.add_argument(
        "gesture",
        nargs="?",
        choices=list(GESTURES),
        help="実行するジェスチャー (省略時は対話モード)",
    )
    return parser.parse_args()


def apply(hand: AmazingHand, name: str) -> None:
    label, method = GESTURES[name]
    print(f"→ {label}")
    getattr(hand, method)()


def interactive(hand: AmazingHand) -> None:
    print("ジェスチャーを入力してください (Ctrl+C で終了)")
    print("  " + ", ".join(GESTURES))
    while True:
        try:
            raw = input("> ").strip().lower()
        except EOFError:
            break
        if not raw:
            continue
        if raw in ("q", "quit", "exit"):
            break
        if raw not in GESTURES:
            print(f"不明: {raw}")
            continue
        apply(hand, raw)
        time.sleep(0.3)


def main() -> int:
    args = parse_args()

    try:
        port = args.port or find_servo_port()
    except RuntimeError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    print(f"ポート: {port}")
    hand = AmazingHand(port)
    hand.enable_torque(True)
    time.sleep(0.3)

    try:
        if args.gesture:
            apply(hand, args.gesture)
            time.sleep(1.0)
        else:
            interactive(hand)
    except KeyboardInterrupt:
        print("\n停止します...")
    finally:
        hand.relax()
        print("サーボをフリーにしました。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

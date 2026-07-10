#!/usr/bin/env python3
"""Amazing Hand (左手) シンプルデモ.

開く → 握る → 広げる → 指差し → ピース を繰り返す。
Ctrl+C で停止し、サーボをフリーにする。

使い方:
  uv run python -m demo.demo
  uv run python -m demo.demo --port /dev/tty.usbmodemXXXX
  uv run python -m demo.demo --once
"""

from __future__ import annotations

import argparse
import sys
import time

from hand import AmazingHand, find_servo_port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Amazing Hand (左手) デモ")
    parser.add_argument(
        "--port",
        default=None,
        help="シリアルポート (省略時は自動検出)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="ジェスチャーを1サイクルだけ実行して終了",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=6,
        help="サーボ速度 1(遅)〜7(速) デフォルト: 6",
    )
    return parser.parse_args()


def run_cycle(hand: AmazingHand) -> None:
    gestures = [
        ("開く", hand.open, 0.8),
        ("握る", hand.close, 1.5),
        ("開く", hand.open, 0.8),
        ("広げる", hand.spread, 1.0),
        ("開く", hand.open, 0.6),
        ("指差し", hand.point, 1.0),
        ("開く", hand.open, 0.6),
        ("ピース", hand.victory, 1.2),
        ("開く", hand.open, 0.8),
    ]

    for name, action, wait in gestures:
        print(f"  → {name}")
        action()
        time.sleep(wait)


def main() -> int:
    args = parse_args()

    try:
        port = args.port or find_servo_port()
    except RuntimeError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        print(
            "  uv run python -m demo.list_ports で利用可能なポートを確認してください。",
            file=sys.stderr,
        )
        return 1

    print(f"ポート: {port}")
    print("Amazing Hand (左手) を初期化中...")

    hand = AmazingHand(port, max_speed=args.speed)
    hand.enable_torque(True)
    time.sleep(0.3)

    print("デモ開始 (Ctrl+C で停止)")
    try:
        while True:
            run_cycle(hand)
            if args.once:
                break
            print("--- 繰り返し ---")
    except KeyboardInterrupt:
        print("\n停止します...")
    finally:
        hand.open()
        time.sleep(0.5)
        hand.relax()
        print("サーボをフリーにしました。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""指の開閉テスト / 中立位置合わせ用スクリプト。

組み立て後の動作確認や、MiddlePos キャリブレーションに使う。

使い方:
  python calibrate.py                     # 全指を順番に開閉
  python calibrate.py --finger index      # 人差し指だけ
  python calibrate.py --middle            # 全指を中立位置へ固定
  python calibrate.py --port /dev/tty.usbmodemXXXX
"""

from __future__ import annotations

import argparse
import sys
import time

from hand import FINGER_IDS, AmazingHand
from ports import find_servo_port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Amazing Hand キャリブレーション / 指テスト")
    parser.add_argument("--port", default=None, help="シリアルポート")
    parser.add_argument(
        "--finger",
        choices=list(FINGER_IDS),
        default=None,
        help="テストする指 (省略時は全指)",
    )
    parser.add_argument(
        "--middle",
        action="store_true",
        help="全指を中立位置に固定して終了",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="開閉の繰り返し回数 (デフォルト: 3)",
    )
    return parser.parse_args()


def test_finger(hand: AmazingHand, name: str, cycles: int) -> None:
    print(f"[{name}] 開閉テスト x{cycles}")
    for i in range(cycles):
        print(f"  cycle {i + 1}: 閉じる")
        hand.move_finger(name, 90, -90, speed=6)
        time.sleep(1.5)
        print(f"  cycle {i + 1}: 開く")
        hand.move_finger(name, -30, 30, speed=6)
        time.sleep(1.0)


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
        if args.middle:
            print("全指を中立位置へ...")
            hand.middle()
            print("中立位置に固定しました。Ctrl+C で終了 (トルク維持)。")
            while True:
                time.sleep(1)
        else:
            fingers = [args.finger] if args.finger else list(FINGER_IDS)
            for name in fingers:
                test_finger(hand, name, args.cycles)
            print("テスト完了。手を開いて終了します。")
            hand.open()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n停止します...")
    finally:
        hand.relax()
        print("サーボをフリーにしました。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

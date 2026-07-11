#!/usr/bin/env python3
"""Amazing Hand を安全な範囲で自動的にアイドリングさせる。"""

from __future__ import annotations

import argparse
import random
import re
import signal
import sys
import time
from collections.abc import Callable

from hand import FINGER_IDS, AmazingHand, find_servo_port

OPEN_ANGLE = (-35.0, 35.0)
FINGERS = tuple(FINGER_IDS)


def parse_duration(value: str) -> float:
    """`30s`, `10m`, `1.5h` を秒へ変換する。単位省略時は秒。"""
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smh]?)\s*", value.lower())
    if not match:
        raise argparse.ArgumentTypeError("時間は 30s / 10m / 1.5h の形式で指定してください")

    amount = float(match.group(1))
    multiplier = {"": 1.0, "s": 1.0, "m": 60.0, "h": 3600.0}[match.group(2)]
    return amount * multiplier


def curled(amount: float) -> tuple[float, float]:
    """開いた位置から中立方向へ amount 度だけ曲げた安全な角度を返す。"""
    amount = max(0.0, min(amount, 30.0))
    return OPEN_ANGLE[0] + amount, OPEN_ANGLE[1] - amount


def finger_twitch(hand: AmazingHand, rng: random.Random, speed: int) -> None:
    """1本の指を小さく曲げて戻す。"""
    finger = rng.choice(FINGERS)
    hand.move_finger(finger, *curled(rng.uniform(10.0, 24.0)), speed=speed)
    time.sleep(rng.uniform(0.5, 1.0))
    hand.move_finger(finger, *OPEN_ANGLE, speed=speed)


def paired_twitch(hand: AmazingHand, rng: random.Random, speed: int) -> None:
    """隣り合う2本の指を少しずらして動かす。"""
    first, second = rng.choice(tuple(zip(FINGERS, FINGERS[1:])))
    amount = rng.uniform(10.0, 20.0)
    hand.move_finger(first, *curled(amount), speed=speed)
    time.sleep(0.15)
    hand.move_finger(second, *curled(amount), speed=speed)
    time.sleep(rng.uniform(0.5, 0.9))
    hand.move_finger(first, *OPEN_ANGLE, speed=speed)
    time.sleep(0.15)
    hand.move_finger(second, *OPEN_ANGLE, speed=speed)


def finger_wave(hand: AmazingHand, rng: random.Random, speed: int) -> None:
    """各指を順番に曲げ、波のように戻す。"""
    fingers = list(FINGERS)
    if rng.random() < 0.5:
        fingers.reverse()
    amount = rng.uniform(12.0, 22.0)

    for finger in fingers:
        hand.move_finger(finger, *curled(amount), speed=speed)
        time.sleep(0.18)
    for finger in fingers:
        hand.move_finger(finger, *OPEN_ANGLE, speed=speed)
        time.sleep(0.18)


def gentle_breathe(hand: AmazingHand, rng: random.Random, speed: int) -> None:
    """全指を浅く曲げて、ゆっくり開く。"""
    amount = rng.uniform(8.0, 16.0)
    for finger in FINGERS:
        hand.move_finger(finger, *curled(amount), speed=speed)
    time.sleep(rng.uniform(0.8, 1.4))
    hand.open(speed=speed)


MOTIONS: tuple[tuple[str, Callable[[AmazingHand, random.Random, int], None]], ...] = (
    ("指を小さく動かす", finger_twitch),
    ("指を小さく動かす", finger_twitch),
    ("2本の指を動かす", paired_twitch),
    ("指を波打たせる", finger_wave),
    ("ゆっくり開閉する", gentle_breathe),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Amazing Hand 自動アイドリング")
    parser.add_argument("--port", default=None, help="シリアルポート (省略時は自動検出)")
    parser.add_argument(
        "--duration",
        type=parse_duration,
        default=None,
        metavar="TIME",
        help="動作時間。例: 30s / 10m / 1.5h (省略時は無制限)",
    )
    parser.add_argument("--seed", type=int, default=None, help="ランダムシード")
    parser.add_argument("--speed", type=int, choices=range(1, 4), default=2, help="速度 1〜3")
    parser.add_argument("--min-interval", type=float, default=3.0, help="動作間隔の最小秒数")
    parser.add_argument("--max-interval", type=float, default=8.0, help="動作間隔の最大秒数")
    parser.add_argument(
        "--cooldown-every",
        type=parse_duration,
        default=600.0,
        metavar="TIME",
        help="クールダウン周期 (デフォルト: 10m、0s で無効)",
    )
    parser.add_argument(
        "--cooldown",
        type=parse_duration,
        default=120.0,
        metavar="TIME",
        help="トルクを切る時間 (デフォルト: 2m)",
    )
    args = parser.parse_args()
    if args.min_interval < 0 or args.max_interval < args.min_interval:
        parser.error("動作間隔は 0 <= min-interval <= max-interval にしてください")
    return args


def sleep_with_deadline(seconds: float, deadline: float | None) -> None:
    if deadline is not None:
        seconds = min(seconds, max(0.0, deadline - time.monotonic()))
    time.sleep(seconds)


def install_signal_handlers() -> None:
    """プロセスマネージャーからの停止要求を安全停止へ変換する。"""

    def request_stop(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, request_stop)


def run_idle(hand: AmazingHand, args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    started_at = time.monotonic()
    deadline = started_at + args.duration if args.duration is not None else None
    next_cooldown = (
        started_at + args.cooldown_every if args.cooldown_every > 0 else None
    )

    while deadline is None or time.monotonic() < deadline:
        now = time.monotonic()
        if next_cooldown is not None and now >= next_cooldown:
            print(f"→ クールダウン ({args.cooldown:g}秒)")
            hand.open(speed=args.speed)
            time.sleep(0.5)
            hand.relax()
            sleep_with_deadline(args.cooldown, deadline)
            if deadline is not None and time.monotonic() >= deadline:
                break
            hand.enable_torque(True)
            hand.open(speed=args.speed)
            next_cooldown = time.monotonic() + args.cooldown_every
            continue

        label, motion = rng.choice(MOTIONS)
        print(f"→ {label}")
        motion(hand, rng, args.speed)
        sleep_with_deadline(rng.uniform(args.min_interval, args.max_interval), deadline)


def main() -> int:
    args = parse_args()
    try:
        port = args.port or find_servo_port()
    except RuntimeError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    print(f"ポート: {port}")
    hand = AmazingHand(port, max_speed=args.speed, close_speed=args.speed)
    install_signal_handlers()

    try:
        hand.enable_torque(True)
        hand.open(speed=args.speed)
        time.sleep(0.5)
        print("アイドリング開始 (Ctrl+C で停止)")
        run_idle(hand, args)
    except KeyboardInterrupt:
        print("\n停止します...")
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            hand.open(speed=args.speed)
            time.sleep(0.5)
        except Exception as exc:
            print(f"警告: 終了位置へ移動できませんでした: {exc}", file=sys.stderr)
        finally:
            try:
                hand.relax()
                print("サーボをフリーにしました。")
            except Exception as exc:
                print(f"警告: トルクを解放できませんでした: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

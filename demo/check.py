#!/usr/bin/env python3
"""Amazing Hand の接続・動作確認。

USB アダプタとサーボ 1〜8 が応答するか調べる。
外部 5V 電源が入っていないとサーボは応答しない。

使い方:
  uv run hand check
  uv run hand check --port /dev/cu.usbmodemXXXX
  uv run hand check --move   # 小さく開閉して実動作も確認
"""

from __future__ import annotations

import argparse
import sys
import time

import numpy as np
from rustypot import Scs0009PyController

from hand import ALL_SERVO_IDS, AmazingHand
from hand.ports import find_servo_port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Amazing Hand 接続・動作確認")
    parser.add_argument("--port", default=None, help="シリアルポート (省略時は自動検出)")
    parser.add_argument(
        "--move",
        action="store_true",
        help="応答したサーボで小さく開閉して実動作も確認する",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=1_000_000,
        help="ボーレート (デフォルト: 1000000)",
    )
    return parser.parse_args()


def check_servo(controller: Scs0009PyController, servo_id: int) -> dict:
    """1 サーボの ping / 位置 / 電圧を取得する。"""
    result: dict = {
        "id": servo_id,
        "ok": False,
        "position_deg": None,
        "voltage": None,
        "error": None,
    }

    try:
        alive = bool(controller.ping(servo_id))
    except Exception as exc:  # noqa: BLE001 - 診断用に広く捕捉
        result["error"] = f"ping: {exc}"
        return result

    if not alive:
        result["error"] = "応答なし (電源・配線・ID を確認)"
        return result

    result["ok"] = True
    try:
        pos = controller.read_present_position(servo_id)
        # rustypot は rad または list を返すことがある
        if isinstance(pos, (list, tuple)):
            pos = pos[0]
        result["position_deg"] = float(np.rad2deg(pos))
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"position: {exc}"

    try:
        volt = controller.read_present_voltage(servo_id)
        if isinstance(volt, (list, tuple)):
            volt = volt[0]
        result["voltage"] = float(volt)
    except Exception as exc:  # noqa: BLE001
        # 電圧は取れなくても位置が取れれば OK 扱い
        if result["error"] is None:
            result["error"] = f"voltage: {exc}"

    return result


def print_report(port: str, results: list[dict]) -> int:
    ok_ids = [r["id"] for r in results if r["ok"]]
    ng_ids = [r["id"] for r in results if not r["ok"]]

    print(f"ポート: {port}")
    print()
    print("ID  状態   位置(度)   電圧")
    print("--  -----  --------  -----")
    for r in results:
        status = "OK" if r["ok"] else "NG"
        pos = f"{r['position_deg']:>7.1f}" if r["position_deg"] is not None else "     -"
        volt = f"{r['voltage']:>5.1f}" if r["voltage"] is not None else "    -"
        line = f"{r['id']:<2}  {status:<5}  {pos}  {volt}"
        if r["error"] and not r["ok"]:
            line += f"  ← {r['error']}"
        print(line)

    print()
    print(f"応答: {len(ok_ids)}/8  (OK: {ok_ids or '-'} / NG: {ng_ids or '-'})")

    if len(ok_ids) == 8:
        print("結果: OK — 全サーボと通信できています")
        return 0

    print("結果: NG — 一部または全部のサーボが応答しません")
    print()
    print("確認ポイント:")
    print("  1. 外部 5V 電源が DC ジャックに入っているか")
    print("  2. ハンド ↔ ドライバ基板のサーボバス配線")
    print("  3. サーボ ID が 1〜8 に設定されているか")
    print("  4. Type-C が抜けていないか / ポートが合っているか")
    return 1


def move_test(port: str) -> None:
    """小さく開いて閉じる実動作テスト。"""
    print()
    print("実動作テスト: 開く → 少し待つ → 中立へ戻す")
    hand = AmazingHand(port, max_speed=4)
    try:
        hand.enable_torque(True)
        time.sleep(0.2)
        hand.open(speed=4)
        time.sleep(1.0)
        hand.middle(speed=4)
        time.sleep(0.8)
        print("実動作テスト: 完了 (指が動いていれば OK)")
    finally:
        hand.relax()


def main() -> int:
    args = parse_args()

    try:
        port = args.port or find_servo_port()
    except RuntimeError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        print("  uv run hand ports でポートを確認してください。", file=sys.stderr)
        return 1

    print("Amazing Hand 接続確認中...")
    try:
        controller = Scs0009PyController(
            serial_port=port,
            baudrate=args.baudrate,
            timeout=0.5,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"エラー: ポートを開けませんでした ({port}): {exc}", file=sys.stderr)
        return 1

    results = [check_servo(controller, servo_id) for servo_id in ALL_SERVO_IDS]
    code = print_report(port, results)

    if code == 0 and args.move:
        move_test(port)
    elif code != 0 and args.move:
        print()
        print("--move はスキップしました (サーボが応答していないため)")

    return code


if __name__ == "__main__":
    raise SystemExit(main())

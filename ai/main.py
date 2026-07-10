"""音声指示で Amazing Hand を動かす CLI。

PC マイクで録音 → gpt-4o-mini-transcribe で文字起こし →
GPT が返答とジェスチャーを決めて手を動かす。

使い方:
  uv run python -m ai.main
  uv run python -m ai.main --port /dev/tty.usbmodemXXXX
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

from ai.agent import respond
from ai.mic import record_until_enter
from ai.transcribe import transcribe
from hand import AmazingHand
from ports import find_servo_port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="音声指示で Amazing Hand を動かす")
    parser.add_argument(
        "--port",
        default=None,
        help="シリアルポート (省略時は自動検出)",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=6,
        help="サーボ速度 1(遅)〜7(速) デフォルト: 6",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "エラー: OPENAI_API_KEY が設定されていません。.env または環境変数を確認してください。",
            file=sys.stderr,
        )
        return 1

    try:
        port = args.port or find_servo_port()
    except RuntimeError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        print("  uv run list_ports.py で利用可能なポートを確認してください。", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)

    print(f"ポート: {port}")
    print("Amazing Hand (左手) を初期化中...")
    hand = AmazingHand(port, max_speed=args.speed)
    hand.enable_torque(True)
    time.sleep(0.3)

    print("音声モード開始 (Ctrl+C で停止)")
    print("各ターン: Enter で録音開始 → 話して → Enter で停止")

    try:
        while True:
            print()
            try:
                wav_bytes = record_until_enter()
            except RuntimeError as exc:
                print(f"録音エラー: {exc}")
                continue

            print("文字起こし中...")
            try:
                text = transcribe(client, wav_bytes)
            except Exception as exc:  # noqa: BLE001
                print(f"文字起こしエラー: {exc}")
                continue

            print(f"あなた: {text}")
            print("考え中...")
            try:
                reply = respond(client, hand, text)
            except Exception as exc:  # noqa: BLE001
                print(f"AI エラー: {exc}")
                continue

            if reply:
                print(f"AI: {reply}")
            else:
                print("AI: (動作のみ)")
    except KeyboardInterrupt:
        print("\n停止します...")
    finally:
        try:
            hand.open()
            time.sleep(0.5)
            hand.relax()
            print("サーボをフリーにしました。")
        except Exception as exc:  # noqa: BLE001
            print(f"終了処理エラー: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

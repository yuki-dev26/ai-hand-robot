"""GPT による返答生成とジェスチャー tool calling。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from hand import AmazingHand

CHAT_MODEL = "gpt-5.4-mini"

GESTURES = ("open", "close", "middle", "spread", "point", "victory")

GESTURE_LABELS = {
    "open": "開く",
    "close": "握る",
    "middle": "中立",
    "spread": "広げる",
    "point": "指差し",
    "victory": "ピース",
}

PROMPT_PATH = Path(__file__).with_name("system_prompt.md")


def load_system_prompt() -> str:
    """ai/system_prompt.md を読み込む。"""
    text = PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError(f"システムプロンプトが空です: {PROMPT_PATH}")
    return text


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "do_gesture",
            "description": (
                "ロボットハンドで指定したジェスチャーを実行する。"
                "動作指示のときは必ずこのツールを呼ぶこと。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": list(GESTURES),
                        "description": "実行するジェスチャー名",
                    },
                },
                "required": ["name"],
            },
        },
    },
]


GESTURE_SETTLE_SEC = {
    "open": 1.0,
    "close": 1.6,
    "middle": 1.0,
    "spread": 1.2,
    "point": 1.2,
    "victory": 1.4,
}

# settle 時間の基準速度 (この速度で GESTURE_SETTLE_SEC を計測した想定)
SETTLE_REF_SPEED = 6
# サーボ音がマイクに入らないよう、動作後に少し待つ
POST_MOTION_QUIET_SEC = 0.5


def gesture_settle_sec(hand: AmazingHand, name: str) -> float:
    """速度に応じたジェスチャー完了待ち秒数を返す。遅いほど長く待つ。"""
    speed = hand.close_speed if name == "close" else hand.max_speed
    speed = max(int(speed), 1)
    return GESTURE_SETTLE_SEC[name] * (SETTLE_REF_SPEED / speed)


def apply_gesture(hand: AmazingHand, name: str) -> None:
    """ジェスチャー名に対応する AmazingHand メソッドを実行し、動き終わるまで待つ。"""
    if name not in GESTURES:
        raise ValueError(f"不明なジェスチャー: {name}")
    label = GESTURE_LABELS[name]
    settle = gesture_settle_sec(hand, name)
    print(f"  → {label} ({name})")
    getattr(hand, name)()
    time.sleep(settle)


def respond(client: OpenAI, hand: AmazingHand, user_text: str) -> str:
    """ユーザー発話に対して返答し、必要ならジェスチャーを実行する。

    すべての動作が終わってから返す (呼び出し側は再録音してよい)。
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": load_system_prompt()},
        {"role": "user", "content": user_text},
    ]

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    message = response.choices[0].message
    reply = (message.content or "").strip()

    moved = False
    if message.tool_calls:
        for tool_call in message.tool_calls:
            if tool_call.function.name != "do_gesture":
                continue
            args = json.loads(tool_call.function.arguments or "{}")
            gesture_name = args.get("name")
            if not gesture_name:
                continue
            apply_gesture(hand, gesture_name)
            moved = True

    if moved:
        time.sleep(POST_MOTION_QUIET_SEC)

    return reply

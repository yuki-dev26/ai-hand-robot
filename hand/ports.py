"""シリアルポート検出ユーティリティ。"""

from __future__ import annotations

import serial.tools.list_ports


def list_ports() -> list[tuple[str, str]]:
    """利用可能なシリアルポートの (device, description) 一覧を返す。"""
    return [(p.device, p.description or "") for p in serial.tools.list_ports.comports()]


def find_servo_port() -> str:
    """バスサーボ用アダプタらしきポートを自動検出する。

    macOS / Linux / Windows でよくある USB シリアル名を優先する。
    見つからない場合は RuntimeError。
    """
    ports = list_ports()
    if not ports:
        raise RuntimeError("シリアルポートが見つかりません。USB アダプタを接続してください。")

    # 優先キーワード (大文字小文字無視)
    preferred = (
        "usbmodem",
        "usbserial",
        "ttyacm",
        "ttyusb",
        "wch",
        "cp210",
        "ch340",
        "ftdi",
        "serial",
    )

    scored: list[tuple[int, str]] = []
    for device, desc in ports:
        text = f"{device} {desc}".lower()
        score = 0
        for i, key in enumerate(preferred):
            if key in text:
                score = len(preferred) - i
                break
        # macOS の Bluetooth 等は除外
        if "bluetooth" in text or "debug" in text:
            score = -1
        scored.append((score, device))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_device = scored[0]
    if best_score <= 0:
        devices = ", ".join(d for _, d in ports)
        raise RuntimeError(
            "USB シリアルらしきポートが特定できません。"
            f"候補: {devices}。--port で明示してください。"
        )
    return best_device

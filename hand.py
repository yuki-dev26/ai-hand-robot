"""Amazing Hand (Left) 制御モジュール.

Feetech SCS0009 サーボ x8 を rustypot 経由で制御する。
公式デモ (pollen-robotics/AmazingHand) の仕様に準拠。

サーボ ID 配置 (左手・単体運用時は右手と同じ ID):
  Index  : 1, 2
  Middle : 3, 4
  Ring   : 5, 6
  Thumb  : 7, 8
"""

from __future__ import annotations

import time
from typing import Sequence

import numpy as np
from rustypot import Scs0009PyController

# 指ごとのサーボ ID (m1, m2)
FINGER_IDS = {
    "index": (1, 2),
    "middle": (3, 4),
    "ring": (5, 6),
    "thumb": (7, 8),
}

ALL_SERVO_IDS = [1, 2, 3, 4, 5, 6, 7, 8]

# 開閉のオフセット角度 (度)。公式デモと同じ値。
OPEN_OFFSET = (-35, 35)
CLOSE_OFFSET = (90, -90)

DEFAULT_BAUDRATE = 1_000_000
DEFAULT_TIMEOUT = 0.5


class AmazingHand:
    """左手 Amazing Hand のシンプルな制御クラス。"""

    def __init__(
        self,
        port: str,
        *,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        middle_pos: Sequence[float] | None = None,
        max_speed: int = 6,
        close_speed: int = 3,
    ) -> None:
        self.port = port
        self.max_speed = max_speed
        self.close_speed = close_speed
        # キャリブレーション後の中立位置 (サーボ 1〜8 のオフセット度)
        self.middle_pos = list(middle_pos) if middle_pos is not None else [0.0] * 8

        self.controller = Scs0009PyController(
            serial_port=port,
            baudrate=baudrate,
            timeout=timeout,
        )

    def enable_torque(self, enable: bool = True) -> None:
        """全サーボのトルクを ON/OFF する。"""
        value = 1 if enable else 2  # 1=On, 2=Off, 3=Free
        for servo_id in ALL_SERVO_IDS:
            self.controller.write_torque_enable(servo_id, value)
            time.sleep(0.001)

    def move_finger(
        self,
        name: str,
        angle1: float,
        angle2: float,
        speed: int | None = None,
    ) -> None:
        """指定した指を動かす。angle は中立位置からのオフセット (度)。"""
        if name not in FINGER_IDS:
            raise ValueError(f"不明な指: {name}. 候補: {list(FINGER_IDS)}")

        speed = self.max_speed if speed is None else speed
        id1, id2 = FINGER_IDS[name]
        idx = (id1 - 1, id2 - 1)

        self.controller.write_goal_speed(id1, speed)
        time.sleep(0.0002)
        self.controller.write_goal_speed(id2, speed)
        time.sleep(0.0002)

        pos1 = np.deg2rad(self.middle_pos[idx[0]] + angle1)
        pos2 = np.deg2rad(self.middle_pos[idx[1]] + angle2)
        self.controller.write_goal_position(id1, pos1)
        self.controller.write_goal_position(id2, pos2)
        time.sleep(0.005)

    def open(self, speed: int | None = None) -> None:
        """手を開く。"""
        speed = self.max_speed if speed is None else speed
        for name in FINGER_IDS:
            self.move_finger(name, *OPEN_OFFSET, speed=speed)

    def close(self, speed: int | None = None) -> None:
        """手を握る。"""
        speed = self.close_speed if speed is None else speed
        for name in ("index", "middle", "ring"):
            self.move_finger(name, *CLOSE_OFFSET, speed=speed)
        self.move_finger("thumb", *CLOSE_OFFSET, speed=speed + 1)

    def middle(self, speed: int | None = None) -> None:
        """全指を中立位置へ。"""
        speed = self.max_speed if speed is None else speed
        for name in FINGER_IDS:
            self.move_finger(name, 0, 0, speed=speed)

    def spread(self, speed: int | None = None) -> None:
        """指を広げる (左手)。"""
        speed = self.max_speed if speed is None else speed
        self.move_finger("index", -60, 0, speed=speed)
        self.move_finger("middle", -35, 35, speed=speed)
        self.move_finger("ring", -4, 90, speed=speed)
        self.move_finger("thumb", -4, 90, speed=speed)

    def point(self, speed: int | None = None) -> None:
        """人差し指で指差し。"""
        speed = self.max_speed if speed is None else speed
        self.move_finger("index", -40, 40, speed=speed)
        self.move_finger("middle", *CLOSE_OFFSET, speed=speed)
        self.move_finger("ring", *CLOSE_OFFSET, speed=speed)
        self.move_finger("thumb", *CLOSE_OFFSET, speed=speed)

    def victory(self, speed: int | None = None) -> None:
        """ピースサイン (左手)。"""
        speed = self.max_speed if speed is None else speed
        self.move_finger("index", -65, 15, speed=speed)
        self.move_finger("middle", -15, 65, speed=speed)
        self.move_finger("ring", *CLOSE_OFFSET, speed=speed)
        self.move_finger("thumb", *CLOSE_OFFSET, speed=speed)

    def relax(self) -> None:
        """トルクを切ってサーボをフリーにする。"""
        for servo_id in ALL_SERVO_IDS:
            self.controller.write_torque_enable(servo_id, 3)  # Free
            time.sleep(0.001)

# hand — 制御ライブラリ

Amazing Hand (左手) のサーボ制御とシリアルポート検出を提供する共通パッケージです。`demo/` と `ai/` から利用します。

## ファイル

| ファイル | 内容 |
|---|---|
| `controller.py` | `AmazingHand` クラス (開閉・ジェスチャー・指単位制御) |
| `ports.py` | シリアルポート一覧・自動検出 |
| `__init__.py` | 公開 API の再エクスポート |

## 主な API

```python
from hand import AmazingHand, find_servo_port

port = find_servo_port()
hand = AmazingHand(port, max_speed=6)
hand.enable_torque(True)
hand.open()
hand.close()
hand.spread()
hand.point()
hand.victory()
hand.middle()
hand.relax()
```

ジェスチャー: `open` / `close` / `middle` / `spread` / `point` / `victory`

## サーボ配置 (左手・単体)

| 指 | サーボ ID |
|---|---|
| Index (人差し指) | 1, 2 |
| Middle (中指) | 3, 4 |
| Ring (薬指) | 5, 6 |
| Thumb (親指) | 7, 8 |

通信: ボーレート `1000000` / Feetech SCS0009

## キャリブレーション

中立位置の微調整が必要な場合は、`AmazingHand(..., middle_pos=[...])` に 8 個のオフセット (度) を渡してください。公式デモの `MiddlePos` と同じ考え方です。

# Amazing Hand (左手) 制御プログラム

[Seeed Studio Amazing Hand (Left Hand)](https://www.seeedstudio.com/Amazing-Hand-Open-Source-3D-Printable-Robotic-Hand-Kit.html) を PC から動かすシンプルな Python プログラムです。

公式仕様 ([pollen-robotics/AmazingHand](https://github.com/pollen-robotics/AmazingHand) / [Seeed Wiki](https://wiki.seeedstudio.com/hand_amazinghand/)) に準拠しています。

## 必要なもの

- Amazing Hand (左手) 本体
- USB シリアルバスサーボドライバ (Waveshare 等)
- **外部 5V / 2A 以上の電源** (USB 給電だけではサーボは動きません)
- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/)

## セットアップ

```bash
cd ai-hand-robot
uv sync
```

これで `.venv` の作成と依存関係のインストールまで完了します。

## 接続

1. ハンドのサーボバスを USB シリアルアダプタに接続
2. アダプタを PC の USB に接続
3. **外部 5V 電源をハンド側に接続** (必須)
4. ポート確認:

```bash
uv run list_ports.py
```

## 使い方

### デモ (おすすめの最初の一歩)

開く → 握る → 広げる → 指差し → ピース を繰り返します。

```bash
uv run demo.py
uv run demo.py --port /dev/tty.usbmodemXXXX   # ポート指定
uv run demo.py --once                          # 1サイクルだけ
```

### ジェスチャー指定

```bash
uv run gesture.py open
uv run gesture.py close
uv run gesture.py              # 対話モード
```

利用可能なジェスチャー: `open` / `close` / `middle` / `spread` / `point` / `victory`

### 音声 AI モード

PC マイクで話した内容を文字起こしし、AI が返答とジェスチャーを決めて手を動かします。

1. プロジェクト直下に `.env` を作成し、OpenAI API キーを設定:

```bash
OPENAI_API_KEY=sk-...
```

2. 起動:

```bash
uv run python -m ai.main
uv run python -m ai.main --port /dev/tty.usbmodemXXXX
```

各ターンで Enter → 話す → Enter。Ctrl+C で停止します。

### 自動アイドリング

指の小さな動きや波打ちをランダムな間隔で繰り返します。可動域と速度を抑え、
10分ごとに2分間トルクを切ってサーボを休ませます。

```bash
uv run idle.py                         # Ctrl+C まで継続
uv run idle.py --duration 30m          # 30分で終了
uv run idle.py --seed 1                # 動作順を再現可能にする
uv run idle.py --port /dev/tty.usbmodemXXXX
```

停止時や通信エラー時は、可能であれば手を開いてからサーボをフリーにします。

### 指テスト / キャリブレーション

```bash
uv run calibrate.py                  # 全指を順番に開閉
uv run calibrate.py --finger index   # 人差し指だけ
uv run calibrate.py --middle         # 中立位置に固定
```

## サーボ配置 (左手・単体)

| 指 | サーボ ID |
|---|---|
| Index (人差し指) | 1, 2 |
| Middle (中指) | 3, 4 |
| Ring (薬指) | 5, 6 |
| Thumb (親指) | 7, 8 |

通信: ボーレート `1000000` / Feetech SCS0009

中立位置の微調整が必要な場合は、`hand.py` の `AmazingHand(..., middle_pos=[...])` に 8 個のオフセット (度) を渡してください。公式デモの `MiddlePos` と同じ考え方です。

## ファイル構成

| ファイル | 内容 |
|---|---|
| `pyproject.toml` | 依存関係・プロジェクト定義 (uv) |
| `hand.py` | 制御クラス |
| `demo.py` | ジェスチャーデモ |
| `gesture.py` | 単発 / 対話 CLI |
| `idle.py` | 安全な小動作を繰り返す自動アイドリング |
| `calibrate.py` | 指テスト・中立位置合わせ |
| `list_ports.py` | ポート一覧 |
| `ports.py` | ポート自動検出 |
| `ai/` | 音声認識 + GPT で手を動かす |

## トラブルシュート

- **動かない**: 外部 5V 電源が入っているか確認
- **ポートエラー**: `uv run list_ports.py` でデバイス名を確認し `--port` で指定
- **一部の指だけ動かない**: サーボ ID が 1〜8 に設定されているか確認 (Feetech 公式ツールで設定)
- **変な方向に動く**: `middle_pos` のキャリブレーションを調整

## 参考

- [Seeed Studio Wiki - AmazingHand](https://wiki.seeedstudio.com/hand_amazinghand/)
- [pollen-robotics/AmazingHand](https://github.com/pollen-robotics/AmazingHand)
- [rustypot (サーボ制御ライブラリ)](https://github.com/pollen-robotics/rustypot)

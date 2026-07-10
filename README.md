# Amazing Hand (左手) 制御プログラム

[Seeed Studio Amazing Hand (Left Hand)](https://www.seeedstudio.com/Amazing-Hand-Open-Source-3D-Printable-Robotic-Hand-Kit.html) を PC から動かす Python プログラムです。

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
uv run hand ports
```

## 構成

| フォルダ | 内容 |
|---|---|
| [`hand/`](hand/) | サーボ制御ライブラリ・ポート検出 |
| [`demo/`](demo/) | デモ・ジェスチャー・アイドル・キャリブレーション |
| [`ai/`](ai/) | 音声認識 + GPT で手を動かす |

各フォルダの詳細は、それぞれの README を参照してください。

## 起動コマンド

すべて `uv run hand <command>` から起動できます。

```bash
uv run hand --help
```

| コマンド | 内容 |
|---|---|
| `hand demo` | ジェスチャーデモ (おすすめの最初の一歩) |
| `hand gesture` | ジェスチャー指定 / 対話 |
| `hand idle` | 自動アイドリング |
| `hand calibrate` | 指テスト / 中立位置合わせ |
| `hand ports` | シリアルポート一覧 |
| `hand ai` | 音声指示で手を動かす |

### デモ

```bash
uv run hand demo
uv run hand demo --port /dev/tty.usbmodemXXXX
uv run hand demo --once
```

### ジェスチャー

```bash
uv run hand gesture open
uv run hand gesture close
uv run hand gesture              # 対話モード
```

利用可能なジェスチャー: `open` / `close` / `middle` / `spread` / `point` / `victory`

### アイドリング

```bash
uv run hand idle
uv run hand idle --duration 30m
uv run hand idle --seed 1
```

### キャリブレーション

```bash
uv run hand calibrate
uv run hand calibrate --finger index
uv run hand calibrate --middle
```

### 音声 AI

先に `.env` に API キーを設定します。

```bash
OPENAI_API_KEY=sk-...
```

```bash
uv run hand ai
uv run hand ai --port /dev/tty.usbmodemXXXX
```

各ターン: 発話 3秒以上 → 無音 1秒で文字起こし → 動作完了後に再録音。Ctrl+C で停止します。

## トラブルシュート

- **動かない**: 外部 5V 電源が入っているか確認
- **ポートエラー**: `uv run hand ports` でデバイス名を確認し `--port` で指定
- **一部の指だけ動かない**: サーボ ID が 1〜8 に設定されているか確認 (Feetech 公式ツールで設定)
- **変な方向に動く**: `middle_pos` のキャリブレーションを調整 ([`hand/README.md`](hand/README.md) 参照)

## 参考

- [Seeed Studio Wiki - AmazingHand](https://wiki.seeedstudio.com/hand_amazinghand/)
- [pollen-robotics/AmazingHand](https://github.com/pollen-robotics/AmazingHand)
- [rustypot (サーボ制御ライブラリ)](https://github.com/pollen-robotics/rustypot)

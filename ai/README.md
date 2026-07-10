# ai — 音声指示モード

PC マイクの音声を文字起こしし、GPT が返答とジェスチャーを決めて Amazing Hand を動かします。

起動コマンドは [ルート README](../README.md#起動コマンド) を参照してください。

```bash
# .env に OPENAI_API_KEY=sk-... を設定してから
uv run hand ai
```

## 処理の流れ

1. Silero VAD で発話切り出し (`mic.py`)
   - 発話 3秒以上 + 無音 1秒で確定 (短い発話は破棄)
2. `gpt-4o-mini-transcribe` で文字起こし (`transcribe.py`)
3. `gpt-5.4-mini` が返答とジェスチャーを選択 (`agent.py`)
4. [`hand/`](../hand/) のジェスチャーを実行し、動き終わるまで待機
5. 再録音へ戻る

## ファイル

| ファイル | 内容 |
|---|---|
| `main.py` | CLI エントリ (録音 → 動作 → 再録音ループ) |
| `mic.py` | Silero VAD による自動発話切り出し |
| `transcribe.py` | 音声文字起こし |
| `agent.py` | GPT + `do_gesture` tool calling |

## 利用可能なジェスチャー

`open` / `close` / `middle` / `spread` / `point` / `victory`

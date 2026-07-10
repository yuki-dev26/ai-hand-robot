# ai — 音声指示モード

PC マイクの音声を文字起こしし、GPT が返答とジェスチャーを決めて Amazing Hand を動かします。

起動コマンドは [ルート README](../README.md#起動コマンド) を参照してください。

```bash
# .env に OPENAI_API_KEY=sk-... を設定してから
uv run hand ai
```

## 処理の流れ

1. マイク録音 (`mic.py`)
2. `gpt-4o-mini-transcribe` で文字起こし (`transcribe.py`)
3. `gpt-5.4-mini` が返答とジェスチャーを選択 (`agent.py`)
4. [`hand/`](../hand/) のジェスチャーを実行

## ファイル

| ファイル | 内容 |
|---|---|
| `main.py` | CLI エントリ (録音ループ) |
| `mic.py` | プッシュ・トゥ・トーク録音 |
| `transcribe.py` | 音声文字起こし |
| `agent.py` | GPT + `do_gesture` tool calling |

## 利用可能なジェスチャー

`open` / `close` / `middle` / `spread` / `point` / `victory`

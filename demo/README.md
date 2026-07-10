# demo — デモ・手動操作

ハンドの動作確認や手動操作向けのスクリプトです。制御本体は [`hand/`](../hand/) を使います。

起動コマンドは [ルート README](../README.md#起動コマンド) を参照してください。

```bash
uv run hand check
uv run hand demo
uv run hand gesture open
uv run hand idle
uv run hand calibrate
uv run hand ports
```

## ファイル

| ファイル | 内容 |
|---|---|
| `check.py` | 接続・サーボ応答の確認 |
| `demo.py` | ジェスチャーデモ |
| `gesture.py` | 単発 / 対話 CLI |
| `idle.py` | 安全な小動作を繰り返す自動アイドリング |
| `calibrate.py` | 指テスト・中立位置合わせ |
| `list_ports.py` | ポート一覧 |

"""OpenAI gpt-4o-mini-transcribe による音声文字起こし。"""

from __future__ import annotations

import io

from openai import OpenAI

TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"


def transcribe(client: OpenAI, wav_bytes: bytes) -> str:
    """WAV バイト列を日本語で文字起こしする。"""
    audio_file = io.BytesIO(wav_bytes)
    audio_file.name = "audio.wav"
    audio_file.seek(0)

    result = client.audio.transcriptions.create(
        model=TRANSCRIBE_MODEL,
        file=audio_file,
        language="ja",
    )
    text = (result.text or "").strip()
    if not text:
        raise RuntimeError("文字起こし結果が空です。もう一度話してください。")
    return text

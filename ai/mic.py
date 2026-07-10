"""PC マイクからのプッシュ・トゥ・トーク録音。"""

from __future__ import annotations

import io
import wave

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000
CHANNELS = 1


def record_until_enter() -> bytes:
    """Enter で録音開始、もう一度 Enter で停止し、WAV バイト列を返す。"""
    input("Enter で録音開始...")
    print("録音中... (Enter で停止)")

    chunks: list[np.ndarray] = []

    def callback(indata: np.ndarray, frames: int, time_info, status) -> None:  # noqa: ARG001
        if status:
            print(f"録音警告: {status}")
        chunks.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        callback=callback,
    ):
        input()

    if not chunks:
        raise RuntimeError("音声が録音されませんでした。")

    audio = np.concatenate(chunks, axis=0)
    # float32 (-1..1) → int16 PCM
    pcm = np.clip(audio[:, 0] * 32767, -32768, 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    return buf.getvalue()

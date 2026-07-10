"""Silero VAD による自動発話切り出し録音。

発話が min_speech_sec 以上続き、その後 min_silence_sec の無音になったら
WAV を返す。短い発話は破棄して聞き続ける。
"""

from __future__ import annotations

import io
import wave
from collections import deque
from typing import Any

import numpy as np
import sounddevice as sd
import torch
from silero_vad import VADIterator, load_silero_vad

SAMPLE_RATE = 16_000
CHANNELS = 1
CHUNK_SAMPLES = 512  # Silero VAD @ 16kHz は 512 samples 必須
CHUNK_SEC = CHUNK_SAMPLES / SAMPLE_RATE

MIN_SPEECH_SEC = 3.0
MIN_SILENCE_SEC = 1.0
# 発話開始直前のバッファ (切り出し欠け防止)
PRE_ROLL_CHUNKS = int(0.5 / CHUNK_SEC)

_model: Any | None = None


def get_vad_model() -> Any:
    """Silero VAD モデルを遅延ロードして再利用する。"""
    global _model
    if _model is None:
        print("Silero VAD を読み込み中...")
        _model = load_silero_vad()
    return _model


def _to_wav_bytes(pcm_float: np.ndarray) -> bytes:
    pcm = np.clip(pcm_float * 32767, -32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def record_utterance(
    *,
    min_speech_sec: float = MIN_SPEECH_SEC,
    min_silence_sec: float = MIN_SILENCE_SEC,
) -> bytes:
    """Silero VAD で発話を切り出して WAV バイト列を返す。

    - 発話開始を検知して録音開始
    - 発話が min_speech_sec 以上あり、無音が min_silence_sec 続いたら確定
    - 短い発話は破棄して再待機
    """
    model = get_vad_model()
    vad = VADIterator(
        model,
        sampling_rate=SAMPLE_RATE,
        min_silence_duration_ms=int(min_silence_sec * 1000),
    )

    pre_roll: deque[np.ndarray] = deque(maxlen=PRE_ROLL_CHUNKS)
    speech_chunks: list[np.ndarray] = []
    in_speech = False
    speech_samples = 0

    print(
        f"聞き取り中... (発話 {min_speech_sec:g}秒以上 → 無音 {min_silence_sec:g}秒で送信 / Ctrl+C で停止)"
    )

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=CHUNK_SAMPLES,
    ) as stream:
        while True:
            indata, overflowed = stream.read(CHUNK_SAMPLES)
            if overflowed:
                print("録音警告: バッファオーバーフロー")

            chunk = indata[:, 0].copy()
            tensor = torch.from_numpy(chunk)

            event = vad(tensor, return_seconds=True)

            if event and "start" in event:
                in_speech = True
                speech_chunks = list(pre_roll)
                speech_samples = sum(len(c) for c in speech_chunks)
                print("  発話開始")

            if in_speech:
                speech_chunks.append(chunk)
                speech_samples += len(chunk)
            else:
                pre_roll.append(chunk)

            if event and "end" in event and in_speech:
                duration = speech_samples / SAMPLE_RATE
                in_speech = False
                vad.reset_states()
                pre_roll.clear()

                if duration < min_speech_sec:
                    print(f"  短すぎる発話を破棄 ({duration:.1f}秒 < {min_speech_sec:g}秒)")
                    speech_chunks = []
                    speech_samples = 0
                    continue

                print(f"  発話確定 ({duration:.1f}秒)")
                audio = np.concatenate(speech_chunks)
                return _to_wav_bytes(audio)
